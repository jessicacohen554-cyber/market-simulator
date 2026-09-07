# Forecast Scenario Readiness Plan — carbon price, national CES, voluntary clean demand, load growth, and system-wide emissions (2026-09)

**Status: PLANNING ONLY** — produced 2026-09-05 from a zero-solve survey of `origin/main`
HEAD `4d4dc6ce` (26 merges past the director's r#39 pin `cf5425f7`). No model code changed,
no LP solved, no default moved, no `ScenarioConfig` field added. Every claim below cites the
file:line it was read from; where the survey found a live defect it is filed here as a finding
for a repair lane, never fixed in this session (CLAUDE.md rule 1 `[R-STRUCT]`, findings-first).

**Owner ask (verbatim, 2026-09-05):** *"Make a plan for any workstreams that are needed to
ensure the market simulation model in this repo will be ready to run different forecast
scenarios. Like I want to test what adding a carbon price does to resource deployment and
dispatch, along with a national clean energy standard as well as increased voluntary demand
for clean energy and higher load growth projections so I want plans to test each of those
mechanisms and understand impact on system wide emissions."*

**Where this plan sits.** It is a lane plan **subordinate to** the Forecast Finalization
Program (`docs/forecast-development-plan-2026-07.md`, "FF plan"): its tier ladder (§2.1),
the full-solve authorization gate §2.1b, the rubric (§3), the standing constraints (§7) and
the director ledger (`docs/handoffs/capx-director-ledger-2026-08.md`) all bind every session
chartered here. It absorbs and extends two earlier lane plans rather than replacing them:
the national CES plan (`docs/handoffs/national-ces-eac-premium-plan-2026-07.md`, Waves 1–2
complete, W4 campaign deferred) and the probability-bounds scenario matrix
(`docs/handoffs/probability-bounds-plan-2026-07.md` §1, the 13-case AEO/IPM matrix).

---

## 0. Bottom line first

**Most of the plumbing exists. What is missing is (i) one mechanism that does not exist at
all (voluntary clean demand), (ii) one that exists only as a price and not as a standard
(the national CES target), (iii) an emissions output surface that stops at one ISO-year
scalar, and (iv) a scenario harness that can express the cases but cannot difference them.
Separately, the program's own governance limits how far out the answer can be read today.**

| Mechanism | Exists today | Reaches dispatch | Reaches deployment (capacity evolution) | Ready to run a scenario? |
|---|---|---|---|---|
| **Carbon price** | Yes — three knobs (`carbon_price`, `carbon_price_path`, `carbon_price_delta`) + state programs (CARB, RGGI) + a default-off mass-cap row | Yes (`assemble_mc`) | Retirement via full `mc`; CCS retrofit and thermal/emerging entry directly; VRE/storage entry only through prices | **Mostly** — but a federal price on a program ISO today *replaces* the state trajectory (a cut for NEISO/CAISO/NYISO), there is no CLI knob, and two seam defects are filed (§2.1) |
| **National CES** | Yes as an exogenous **premium** (`federal_ces_*`, POC-proven on ERCOT 2026–2030); **no** as a target-share **standard** | Yes (EAC credit on offers) | Yes (entry/retirement/retrofit through the no-stack `max()`) | **Premium ladder: yes. Target standard: no** — the endogenous CES row (CES plan Wave 5) was never built; there is no national target field and no cross-ISO allocation |
| **Voluntary clean demand** | **No** — no field, constant, or module in `src/market_sim/`; corporate PPA demand was adjudicated inadmissible *as a calibrated driver* (`ffr-5b`) | — | — | **No.** Needs a new mechanism (§3.3) and an owner ruling that a *declared scenario axis* is a different admissibility class from a fitted driver |
| **High load growth** | Yes — `demand_growth_path` low/mid/high + the data-center block (`datacenter_load_path`, default `mid`); electrification layers built but default-off and empty outside one NEISO cell | Yes | Yes (peak-anchored backstop + reserve floor; entry only via prices) | **Yes for a first pass** — but the high case is a flat scalar per era, DC siting is PJM-only, and the adequacy invariants (I7/I12/I3) already fail at `mid` load in four ISOs |
| **System-wide emissions** | Per-ISO annual scalar `emissions_mt` only | — | — | **No** — no by-class / by-zone / hourly CO2, no six-ISO rollup, imports excluded by design, matrix frame carries only `emissions_mt` and no case-vs-reference delta |

**The governance fact that shapes everything:** the FF plan §2.1b caps every forecast
invocation at **5 solve-years** unless the ISO's four-leg gate is open. As of 2026-09-05 the
gate is open for **NEISO only** (spent twice: GOLDEN-1/2; GOLDEN-3 in flight under lane D60),
**NYISO's campaign is authorized (Q45) but its start precondition — the `complete` marker —
was withdrawn again the same day** (nyiso-193, board headline), and ERCOT / PJM / CAISO /
MISO are closed on leg (b) (T1-F rubric) or legs (a)+(b). So a 2026–2050 answer to *"what
does a carbon price do to deployment"* is obtainable today for NEISO, soon for NYISO, and
for the other four only after their T1-F structural blockers (the I7/I12 adequacy family
and I3 slack) clear — which this plan does **not** charter (that is the capx director's
queue). What this plan makes ready, ISO-agnostically, is: every mechanism expressible,
wired end-to-end, proven at T0/T1 scale with a paired-response invariant, and reported at
the emissions grain the question needs — so that when a gate opens, the campaign is a
config file and a budget, not a build.

**Workstreams (§3), in dependency order:**

| WS | Name | Kind | Blocks |
|---|---|---|---|
| **WS-0** | Emissions accounting + scenario harness (foundation) | code, zero-solve + T0 | every campaign |
| **WS-1** | Carbon price — federal-price semantics repair + seam defects + six-ISO paired probe | code + T0/T1 | carbon campaign |
| **WS-2** | National CES — endogenous target row + national clearing post-processor (+ re-prove the premium ladder at HEAD posture) | code + T1 | CES campaign |
| **WS-3** | Voluntary clean demand — new mechanism (annual volumetric attribute demand with a willingness-to-pay ceiling) | design memo → code + T0 | voluntary campaign |
| **WS-4** | High load growth — coherent high case, DC siting, adequacy posture, optional published-forecast intake | code + T1 | load campaign |
| **WS-5** | Campaign execution — the case set, the tier staging, registration, the emissions synthesis memo | solves (gated) | the answer |

Owner decision boxes are collected in §6; session prompts in §7.

---

## 1. What "ready to run a scenario" means (definition of done, per mechanism)

A mechanism is scenario-ready when **all** of the following hold. This is the checklist
every WS-1…WS-4 session closes against, and §5's scorecard tracks it.

1. **Expressible in a committed config.** The scenario is a `configs/scenarios/*.yaml` +
   a `configs/*_matrix.yaml` `cases:` entry — every lever a registered `ScenarioConfig`
   field with a citation, visible in `run_config.json` (rules 5 `[R-NO-MAGIC]`, 24
   `[R-REGISTRY]`). No env-var, no CLI-only knob.
2. **Reaches both halves of the model.** The lever moves the dispatch LP (offers, a
   constraint row, or demand) **and** the capacity-evolution screens (retirement / entry /
   retrofit / backstop), each through an existing seam — never a second mechanism for the
   same phenomenon (rule 19 `[R-ONE-MECH]`).
3. **Right-signed and right-sized on a paired probe.** A paired T0 run (base vs arm,
   one lever moved) passes its paired invariant in every ISO where the lever is live —
   P1-style for carbon (`scripts/check_forecast_invariants.py:899`), and a new paired
   check per mechanism (§3). The check is **structural** (direction, order of magnitude,
   footprint confined to the claimed rows) — never "did the residual move" (rule 29
   `[R-SCREEN]`).
4. **Backcast byte-identity.** Every new field coerces to its inert value in
   `mode="backcast"` (the `datacenter_load_path` / `carbon_price_delta` pattern,
   `scenarios.py:15545-15555`, `:15739-15746`), every keeper cache key is unchanged, and
   the field is registered in `_CACHE_KEY_OPTIONAL_FIELDS` at its inert default so
   pre-existing forecast keys stay stable.
5. **Matrix duty discharged.** A new solve-affecting field has its row in
   `docs/codebase-site/data/mechanism-matrix.js` and a cell line in all six ISO shards in
   the same PR (rule 28 `[R-MECH-MATRIX]`, CI-enforced by `scripts/check_mechanism_matrix.py`).
6. **Emissions readable at the required grain** (WS-0): annual CO2 by ISO, by fuel class,
   by zone; cumulative; delta vs the reference case; unserved energy alongside.
7. **Registered.** Probe and campaign runs go to the forecast namespace via
   `scripts/register_forecast_run.py` (kind `t1f` / a new `scenario` kind) — never the
   backcast registry (FF plan §7.5).

---

## 2. Current state, per mechanism (verified at HEAD `4d4dc6ce`)

### 2.1 Carbon price

**Built.**
- Three config levers, `src/market_sim/config/scenarios.py:2692-2715`: `carbon_price`
  (flat $/t, **replace** semantics — owner ruling Q26 keeps it, with the D34 below-base
  guard at `:15572-15575`), `carbon_price_path` (`zero/low/mid/high` → the RFF knots in
  `config/fuel_trajectories.py:1132-1137`: mid 0→15→35→50 $/t at 2026/2030/2040/2050; high
  0→30→70→110), `carbon_price_delta` (additive on the resolved signal, forecast-only,
  built by capx-D26 for the FC-6 paired arm). `policy_bundle` (`:2716`) resolves `tight`
  → `carbon_price_path="mid"` + IRA +5 yr, `rollback` → zero + `state_carbon_pricing=False`
  + IRA −2 yr (`config/scenario_resolvers.py:250-267`).
- Resolver precedence, `policy/carbon.py:44-89`: (1) nonzero `carbon_price` replaces;
  (2) else the state program adder from `policy/cap_and_trade.py::resolve_carbon_program`
  — measured allowance prices in backcast, in forecast the **projected** trajectory
  (last measured price escalated at the program's 7 %/yr containment-band rate,
  `cap_and_trade.py:146-164`; NEISO reads $26.05/t in 2026 → $132.16/t in 2050 per
  D23 §2); (3) else the RFF path; then `+ carbon_price_delta`.
- Marginal cost: `mc = hr·fuel + vom + emission_rate·carbon_price + …`
  (`data/fleet/legacy_bins.py:303-347`, the multiply at `:340`); per-unit CO2 rates from
  the CAMPD-derived forward estimator (`data/emission_rates.py:155`, CLAUDE.md "forecast
  vs backcast").
- Capacity evolution: threaded at `runner.py:2173-2190` into `evolve_fleet`. Retirement
  sees carbon through the full `mc` (`retirements.py:2842`); CCS retrofit directly
  (`capacity_evolution/ccs.py:391-397`, 45Q stacked at `:405-407`); thermal and emerging
  new entry directly (`new_entry.py:1246-1250`, `:331-356`). **Wind/solar/storage entry
  has no carbon argument** (`new_entry.py:525-530`, `model/storage.py:1836`) — they respond
  only through the prior-year LP prices the screen reads. That is the correct economics
  (a carbon price reaches a zero-carbon builder only through the energy price), not a gap.
- Mass-cap row (`mass_cap_enabled`, default off; `policy/constraints.py`, dual =
  `DispatchResult.co2_cap_price`) — the cap-and-trade alternative to a price, implemented
  and tested, never armed in a forecast campaign.
- Tests: 42 in `tests/unit/policy/test_cap_and_trade.py`, 12 in
  `test_carbon_price_below_base_guard.py`, plus the emerging-tech / CCS / capacity suites.
- Existing evidence: the NEISO FC-6 P1 pair (`carbon_price_delta=25`) **passes** —
  cumulative 2026–2050 CO2 210.52 → 174.96 Mt (−16.9 %), prices up every year, more CCS
  (`FINDING-capx-d26-p1-arm-construction-2026-09-01.md`). Only NEISO has ever been run.

**Gaps and defects (filed, not fixed).**

- **G-C1 (design defect, live in the shipped `tight` bundle).** In forecast mode an
  explicit non-`zero` `carbon_price_path` **suppresses** the state program adder
  (`cap_and_trade.py:289-291`: `price = None`). On the three program ISOs the projected
  program trajectory exceeds every RFF path in every year (NEISO RGGI $26→$132/t vs RFF
  mid $0→$50/t; CAISO CARB ≈$28/t escalating 7 %/yr vs the same), so
  `policy_bundle="tight"` — and any "add a federal carbon price" scenario written with
  `carbon_price_path` — is a **carbon-price CUT** on CAISO / NYISO / NEISO. It is the D23
  premise inversion again, one field over, and the D34 guard does not fire on it (the
  guard reads `carbon_price`, not the path). The `tight`/`rollback` bundle definitions
  were written before the EM-6 seam made forecast program prices non-zero. **This is
  WS-1's first deliverable**; the recommended repair is a **floor** combination
  (effective = max(federal path, program trajectory)), see §6 D-1.
- **G-C2 (seam defect).** `model/interchange/spec.py:1931` builds the CAISO border-carbon
  adder from the raw field `config.carbon_price`, not `resolve_carbon_price`; under the
  default program-resolved posture (`carbon_price=0.0`) that seam's adder is $0. Every
  other border site uses the resolver (`runner.py:1321`, `interchange/caiso.py:458`,
  `import_nodes.py:393`). Reproduce, then fix in WS-1.
- **G-C3 (forecast-path asymmetry).** The forecast orchestrator passes a scalar to
  `assemble_mc` (`runner.py:2561-2575`); the membership-weighted per-generator column
  (PJM's partial RGGI footprint) is built only in `scripts/run_calibration.py:4022-4052`.
  Inert today (PJM's forecast adder is $0 — `projected_price` has no PJM anchor,
  `cap_and_trade.py:157-159`), live the moment a federal price with per-state stacking or
  the PJM RGGI gate is armed in forecast. Fix in WS-1 with the floor repair.
- **G-C4.** No CLI knob on any forecast runner (`run_full_horizon.py`'s 21 flags carry no
  carbon field); carbon is YAML / matrix-case only. Acceptable — the harness IS the YAML
  — but WS-0 adds a generic `--set field=value` override so a probe never needs a new file.
- **G-C5.** New thermal entry prices carbon at the best-in-class `CO2_RATES` bin
  (`new_entry.py:1246`), not a per-plant rate — correct for a new unit; noted for
  disclosure only.
- **G-C6 (open behavioural question, director ledger `:1198`).** ERCOT clears 14 CCS
  retrofits / 2,741.8 MW at carbon = 0 on 45Q alone in some vintages; D50's
  `ccs_retrofit_capex_co2_scaling` default (2026-09-05) closes it at carbon 0 for ERCOT
  and MISO. A carbon scenario re-opens the retrofit screen with a price — the D30/D41/D50
  chain is the reference for reading that response.

### 2.2 National clean energy standard

**Built.**
- The **federal CES premium** layer, `policy/federal_ces.py` + `ScenarioConfig`
  `federal_ces_*` (`scenarios.py:3084-3157`): master gate (forecast-only; raises in
  backcast at `:15584-15589`), premium $/MWh real-2026 with real escalation or sparse
  knots, two crediting modes (`clean_capture` default: zero-carbon fuels 1.0, CCS at the
  0.95 capture fraction, unabated fossil 0; `cesa_ci` variant: `clip(1 − CI/0.82, 0, 1)`
  with the 0.45 t/MWh unabated-CC cutoff), eligible-fuel list (nuclear, wind, solar,
  hydro, geothermal, offshore wind, gas_cc_ccs, hydrogen CT/CCGT), storage ineligible,
  `federal_ces_replaces_state_rps` counterfactual.
- Wiring: dispatch (offer credit through `policy/eac.py:92-100`, `:142-160`), entry and
  retirement (`new_entry.py:1460-1480`, `retirements.py:3152-3184`) through the no-stack
  `max(EAC, RPS dual, clean-tier dual)` rule, CCS retrofit seam (W2-C).
- Campaign machinery: `configs/ces_premium_matrix{,_ci,_poc}.yaml` (BAU + {10, 20, 30}),
  `scripts/run_ces_leg.py` (one leg per invocation, §2.1b-clean), `market-sim matrix`,
  `scripts/report_ces_campaign.py` (nine per-ISO delta tables vs BAU),
  `scripts/generate_financial_reports.py` (plant/company revenue deltas; fixed to run on a
  fresh checkout by FF-3F).
- POC evidence (ERCOT 2026–2030, `ff-3b-ces-poc-2026-07.md`): the premium moves the whole
  surface — 2030 clean share 0.400 → 0.492 → 0.506 at $0/$20/$40, negative-price hours
  0 → 1017 → 1111, solar captured price $30 → $12 → $1.36/MWh. Machinery-only; no
  premium-ladder conclusion was drawn.
- State RPS as an annual LP row whose dual is the REC price (`model/lp/rows.py:27-95`;
  targets in `config/capacity_market.py:4275-4442`; ACPs `:4500-4506`); MISO additionally
  carries per-state compliance-region rows and **clean-tier rows that admit nuclear**
  (`policy/clean_tiers.py`, `rows.py:145-202`), armed via `iso_configs.py:1083-1087`.

**Gaps.**

- **G-S1 (the standard itself).** There is **no** national CES *target*: no config
  field for a clean-share target, no national-target constant, no cross-ISO allocation,
  and the endogenous CI-weighted CES row (CES plan §1 "Wave 5, optional") was never built
  (grep for it in `src/` returns nothing). The model can answer "what does premium $X do"
  but not "what premium (or what deployment) does an 80 %-by-2035 standard imply" except
  by reading the ladder's response curve by hand.
- **G-S2 (scope).** Every RPS/clean row lives inside one ISO's LP (`runner.py:1195-1229`,
  `policy/rps.py:120-121`); a national certificate market cannot clear inside it (CES plan
  §1). Two bracketing representations are available and neither is built end-to-end:
  **uniform price** (the premium ladder; equivalent to unconstrained cross-ISO credit
  trade) and **uniform share** (each ISO carries the national % as its own row; equivalent
  to no cross-ISO trade). The gap between them is the cross-ISO-trade uncertainty and is
  itself a result worth reporting.
- **G-S3 (row coupling).** The clean-tier row family — the natural carrier for a
  nuclear-admitting CES row — is built only when the RPS *region* family is armed
  (`rows.py:1346`, "requires the RPS region family"), which exists only for MISO. A federal
  row spanning all zones needs that coupling relaxed.
- **G-S4 (readiness).** The W3-R readiness verdict for the 2026–2050 CES campaign is
  **NO-GO** on R1 (ERCOT solar entry exactly 0 GW vs 25.08 actual in hindcast) and R2
  (ERCOT exit composition inverts onto gas_st) (`ces-w3r-readiness-2026-07.md`). Both are
  capacity-screen defects in the capx director's queue, not CES defects; a CES *dispatch*
  response is trustworthy now, a CES *deployment* response in ERCOT is not until they clear.
- **G-S5 (records).** The three CES-POC sidecars the POC doc names
  (`frontend/data/hindcast/ercot-2026-2030-ces-poc-*.json`) are not in the tree — removed
  by the 2026-09-05 keeper-only prune. The POC survives as a handoff doc only; WS-2 re-runs
  it at the HEAD posture, which is needed anyway (every default flip since July moved it).
- **G-S6.** `policy/constraints.py` names RPS in its docstring but implements only the
  mass cap — a docs fix for `/sync-docs`, no code.

### 2.3 Voluntary clean energy demand

**Built: nothing.** No `ScenarioConfig` field, constant or module for voluntary demand,
corporate PPA volume, hourly-matched / 24/7 procurement, voluntary REC demand or green
tariffs anywhere in `src/market_sim/` (the only hits are comments: ERCOT voluntary TX RECs
"~$1–3/MWh, immaterial", `scenarios.py:8983`, `:9021`). The seven `eac_price_*` scalars
(`scenarios.py:3063-3074`) are exogenous *prices* with no year or ISO dimension, all 0.0,
set by no committed config. The 24/7 CFE machinery exists only in the deliberately isolated
`scope2-lce-portfolio/` tool, which imports nothing from `market_sim` and consumes the
simulator's LMPs as a file (`docs/scope2-lce-portfolio.md`).

**The standing ruling that governs this.** `docs/handoffs/ffr-5b-procurement-channel-design-2026-08-05.md`
§1.4 adjudicated *corporate PPA demand* **inadmissible as an entry driver**: (a) the volume
series (BNEF, LevelTen, S&P) are proprietary, so they cannot enter `data/raw/` re-queryably
(rule 13 reproducibility); (b) no published forward series exists at ISO grain, so a forward
number would be a free parameter (rule 20 `[R-DOF]`); (c) the realized half is already in
the EIA-860 proposed pipeline. That ruling is about a *calibrated driver* — a quantity the
model would be tuned against. **A scenario axis is a different admissibility class**: an
explicitly-labelled, disclosed what-if input whose levels come from public anchors and
whose whole point is to be moved — the same class as `carbon_price_path` (RFF paths) and
`datacenter_load_path` (ISO queue reports). It needs no identification and creates no DOF
in the calibrated model because it is coerced inert in backcast. Whether the owner accepts
that distinction is **decision D-3** (§6); this plan proceeds on the assumption it is
accepted and states the public anchors it would use (§3.3).

**Also relevant.** Unmodelled long-term contracting (utility IRP/RFP + corporate PPAs
against the ITC) is a repeatedly disclosed residual behind under-built MISO/PJM solar
(`ffr-3v-miso-entry-screen-2026-08-04.md:64,410,818`, `forecast-readiness-prompt-pack-2026-07.md:2723`).
A voluntary-demand row is the structurally faithful way to give that channel a home
(rule 1): a buyer with a willingness to pay above the energy price, whose demand enters
the entry screen as an attribute price exactly the way the RPS dual does today.

### 2.4 Load growth

**Built.**
- `demand_growth_path` low/mid/high (`scenarios.py:2811`) → `DEMAND_GROWTH_RATES`
  (`config/constants.py:2533-2627`, per-ISO near/long eras with `DEMAND_GROWTH_TRANSITION_YEAR
  = 2030`), cited to ERCOT 2025 LTLF, CEC 2025 IEPR, PJM 2026 LTLF, NYISO 2026 Gold Book,
  ISO-NE 2026 CELT, MISO Sept-2025 LTLF. High near-era rates: ERCOT 11.5 %/yr, CAISO 4.2,
  PJM 6.0, MISO 4.5, NYISO 2.6, NEISO 2.2. Continuous `demand_growth_percentile` for the
  sampler; `demand_growth_vintage` for as-known hindcasts.
- The **data-center block** (`datacenter_load_path`, default `mid` since FF-1F;
  `data/datacenter.py:239-320`): a flat 0.85-CF block relocated energy-invariantly out of
  the DC-inclusive growth, trajectories in `DATACENTER_ADDITIONS_MW` (`constants.py:2858+`;
  ERCOT mid 37 GW / high 122 GW by 2030, PJM mid 30 GW), zone shares for PJM
  (`DATACENTER_ZONE_SHARE`, Dominion 0.55 anchor), **ERCOT** (a full published
  per-weather-zone decomposition since 2026-07-21 — this line previously read "only for PJM",
  corrected by SCN-WS4a 2026-09-05 after verifying it at this plan's own pin) and **MISO**
  (the 2026 LTLF regional DC decomposition, SCN-WS4a); NEISO `{}` (re-confirmed against the
  2026 CELT with the arithmetic written out, `FINDING-scn-ws4a-2026-09-05.md` §3).
- **Electrification end-use layers** (FF-G4 Option B, `electrification_path`,
  `scenarios.py:2872`): built, default `off`, populated in exactly one cell (NEISO
  heat_pump mid, `constants.py:3078-3139`); `ev` empty in every ISO; the hourly-profile
  registry is fail-closed and empty (`datacenter.py:406-412`).
- Load feeds capacity evolution through the post-layer `peak_demand` (`runner.py:1956-1958`)
  into the reserve-margin backstop (`capacity_evolution/adequacy.py:850-931`; armed iff the
  ISO has a capacity market, so **off for ERCOT**) and the retirement reliability floor;
  the entry screen sees load only through prior-year prices.

**Gaps.**

- **G-L1.** Growth is **one flat scalar per era applied to every zone and every hour**
  (`runner.py:401-463`). Peak-CAGR ≡ energy-CAGR by construction except where the DC block
  (flattening) or the one NEISO heat-pump layer (peaking) reshapes it. A "high load"
  scenario today is a DC-shaped high case, which is the published reality for ERCOT/PJM/MISO
  (DC-dominated growth) and a disclosed simplification for CAISO/NYISO/NEISO
  (electrification-dominated). `model-methodology-spec.md:728,801,822` still documents only
  the scalar.
- **G-L2. CLOSED 2026-09-06 by SCN-LOAD**, executing owner ruling **S4** (card D-4: *fund
  the full datatype*). All six published forecasts are now under
  `data/raw/load-forecast/<iso>/` behind the curated `load-forecast` datatype
  (`data/dictionary/schema/load-forecast.schema.yaml`,
  `scripts/data/curate_load_forecast.py`), and `DEMAND_GROWTH_RATES`,
  `DATACENTER_ADDITIONS_MW` and `ELECTRIFICATION_LAYERS` are **derived from it rather than
  hand-transcribed**. Four of six ISOs are a native workbook parse (a vintage refresh is
  drop-in-and-re-run); NYISO and MISO are transcriptions validated against numbers their
  own publications print. The 2026 Gold Book was not absent but a gitignored corpus
  payload — re-fetched and sha256-verified byte-exact.
  **It was NOT only a provenance upgrade.** The intake found two defects a transcription
  could not see: every rate's near era was measured to 2030 when the model's resolver
  applies it to 2031, and the table was silently mixing peak- and energy-derived bases.
  Correcting both moves forecast demand by up to **+31 % at 2030** (ERCOT mid), while
  NYISO — the one row already properly derived — reproduces to four decimal places.
  Four "no published source" comments were also found stale (PJM Table B-9b, NYISO's
  end-use energy series, ERCOT's EV component, NYISO's and MISO's low cases).
  Full closure table, movement at full magnitude and six routed items:
  `docs/handoffs/FINDING-scn-load-2026-09-06.md`. **Still open:** MISO's driver-level
  per-LRZ data behind the 403-walled `www.misoenergy.org` host, and
  `DEMAND_GROWTH_TRANSITION_YEAR` (G-D4-5), which has no published source and stays a
  disclosed null.
- **G-L3 (coherence of the high case).** `demand_growth_path=high` and
  `datacenter_load_path=high` are independent axes; ERCOT `high` DC (122 GW by 2030)
  exceeds the grown energy and drops into the additive tail regime
  (`datacenter.py:318-320`). The high-load scenario needs a *declared* pairing (§3.4). **DECLARED 2026-09-06 by SCN-WS4b**: `LOAD-HI` / `LOAD-HI-ORGANIC` in the campaign YAML, with the tail-regime arithmetic in the case comment — under `high` ERCOT stays in the relocate regime through 2029 (block 52–95 % of energy, peak *below* REF) and flips to the tail regime in 2030 alone (E 800 → 1,800 TWh, peak 94 → 267 GW in one year); the ORGANIC companion is byte-identical to `LOAD-HI` on PJM/CAISO/NEISO through 2030 (`FINDING-scn-ws4b-2026-09-06.md` §3).
- **G-L4 (adequacy response).** At `mid` load the T1-F FC-1 fail sets already read
  ERCOT {I12, I3} · CAISO {I12, I3, I7} · PJM {I7, I12} · MISO {I3} (board `gate_reading`,
  2026-09-05). Higher load pushes the same invariants harder: in ERCOT (no backstop) it
  shows up as **unserved-energy slack**, in curve-ON ISOs as backstop gas_ct. A CO2 number
  read under binding slack is understated by the shed energy — WS-0 reports unserved
  energy beside CO2 and WS-4 pre-declares how each ISO's high case is read. **PRE-DECLARED 2026-09-06 (SCN-WS4b, `load-hi-adequacy-reading-2026-09-06.md` §5)**; at that pin the bare `ff-verdicts.json` keys read ERCOT {I12, I3} · CAISO {I12, I7} · PJM {I12, I7} · MISO {I12, I7} · NEISO {} · NYISO {} — the CAISO/MISO sets differ from the board's `gate_reading` prose quoted above (routed, FINDING §5 item 1). The report's headline frame now carries `backstop_built_mw` / `backstop_built_mwh` beside `unserved_mwh`.
- **G-L5.** `datacenter_percentile` / `electrification_percentile` are documented as
  sampler levers but `uncertainty.py:264-270, 425-448` never draws them. Records only.

### 2.5 Emissions accounting and the scenario harness

**Built.**
- `results/emissions.py`: hourly system CO2 (`compute_emissions`, `:17`), attributional
  fossil average rate (`:33`), NOx/SO2, reporting-only startup CO2 (default off), CHP
  must-run reconstruction. Annual `emissions_mt` scalar in `results/export.py:135-137`,
  `:198-210`; per-ISO JSON via `export_scenario_json`; `co2_mt` per year in
  `full_horizon_summary.json` (`scripts/run_full_horizon.py`, reconstructed as
  `dispatch × emission_rate` because `DispatchResult.emissions` is never populated,
  `:374-390`).
- Forecast-year rates: the CAMPD-grounded forward estimator for existing units
  (`data/emission_rates.py:155`), static `CO2_RATES` best-bin for new thermal
  (`new_entry.py:663-716`), `(1 − capture)` for CCS.
- Harness: `market-sim matrix --config <base> --matrix <cases.yaml> --iso --workers ≤2`
  (`runner.py:4919`; `src/market_sim/matrix.py`), `sweep` (cartesian), `ensemble`
  (weather years / PB-2 sampler + PB-3 structural prior), `run_ces_leg.py` (one case per
  invocation), `register_forecast_run.py` (the single registration path),
  `collate_full_horizon.py` (per-ISO tables). Cache: `results/{iso}/{cache_key}/year_*.parquet`.
- Dashboard: `forecast-runs.html` shows a per-run CO2 (Mt) sparkline and the T1-X CO2
  skill table; the crossover CO2 scorer is grain-repaired (D5-R).

**Gaps.**

- **G-E1.** No CO2 **by fuel class**, **by zone**, or **hourly** in any persisted output
  (class-grain CO2 exists only inside the crossover scorer, `score_crossover.py:302`).
  "What does a carbon price do to *dispatch*" needs the class grain; "where" needs the zone
  grain.
- **G-E2.** No **six-ISO rollup**. `collate_full_horizon.py` writes one row per ISO and
  never sums. "System-wide" must be defined (§3.0): the six modeled ISOs, ≈ two-thirds of
  US load; SPP, the Southeast and the non-ISO West are outside the model and stay outside
  the number.
- **G-E3.** **Imports carry zero emissions by design** (`import_nodes.py:100-104`: the
  carbon cost rides the tranche VOM "without the import MWh inflating the modeled in-state
  CO2 total"). CAISO WECC and NEISO HQ imports are 10–30 % of those ISOs' energy. A
  scenario that shifts imports moves real emissions the number does not see. WS-0 adds a
  **reported-only** import-emissions line (CARB unspecified EF for CAISO, an explicit
  hydro/zero EF for HQ), never folded into the calibration-scored total.
- **G-E4.** `matrix.py::build_matrix_frame` carries **only `emissions_mt`** and emits a
  min/max envelope, **no case-vs-reference delta** table (`matrix.py:113-178`). Per-case
  differencing exists only inside `report_ces_campaign.py`, keyed to the CES premium.
- **G-E5.** No committed scenario YAML varies any policy or driver axis (all eight
  `configs/scenarios/*.yaml` vary only ISO, horizon and `entry_screen_diagnostics`); no
  CAISO / MISO / NYISO / NEISO scenario YAML exists at all.
- **G-E6.** No marginal emission rate anywhere (`data/campd.py:1073` decomposes the measured
  marginal/no-load CO2; dispatch uses a flat rate). Attributional CO2 is the right basis for
  the owner's question (the delta between two full-system runs IS the consequential
  number); noted for disclosure.
- **G-E7.** NOx/SO2 are computed but not exported, scored or dashboarded (CO2-rate plan
  §7 deferral). Out of scope here unless the owner wants criteria pollutants.

---

## 3. Workstreams

Conventions: every session is a fresh branch off `origin/main`, `[FABLE]` for structural /
adjudication work and `[OPUS]` for pre-declared execution (director doctrine r#20); every
solve-carrying session writes a PRECOMMIT before its first solve (rule 29) and a FINDING
after; every session cites the mechanism matrix and its ISO's lever queue and updates the
cells it touches (rule 28). Solves in-session, never on CI runners.

### 3.0 Definitions the whole plan uses

- **System-wide emissions** = Σ over the six modeled ISOs of annual attributional CO2 from
  in-ISO generation (`emissions_mt` basis), reported with three disclosed side lines that
  are never added into it: (i) import-attributed CO2 (G-E3), (ii) unserved energy in MWh
  (G-L4), (iii) the ISOs *not* modeled. Cumulative 2026–2050 and per-year; delta vs the
  reference case per ISO and summed.
- **Reference case (REF)** = the ISO's shipped forecast posture at the campaign's frozen
  HEAD (`policy_bundle="current"`, `demand_growth_path="mid"`, `datacenter_load_path="mid"`,
  `federal_ces_enabled=False`, carbon = the resolved state trajectory or zero). Every
  delta is against REF; REF is solved once per ISO per campaign and reused (FF plan §2.4
  rule 3).
- **Dispatch response** = the change in generation by fuel class, prices, curtailment and
  CO2 on the *same* fleet — read from the first solve-year of a scenario (2026) and from
  paired T0 runs. **Deployment response** = the change in builds / retirements / retrofits
  / storage by year — needs the horizon and is the §2.1b-gated half.

### WS-0 — Emissions accounting + scenario harness (foundation) `[OPUS]`, zero-solve + T0

Owned files: `results/emissions.py`, `results/export.py`, `results/outputs.py`,
`src/market_sim/matrix.py`, `scripts/collate_full_horizon.py`, a new
`scripts/report_scenario_deltas.py`, `scripts/run_full_horizon.py` (override flag only),
`configs/scenarios/`, `scripts/register_forecast_run.py` (new `kind`), dashboard pages.

1. **Emissions grain.** In `export.py::_summarize_year` add `emissions_by_fuel_mt`
   (dict, same fuel keys as `generation_twh`) and `emissions_by_zone_mt`, computed from the
   cached `dispatch × FleetContext.emission_rate` at read time exactly as `co2_mt` is today
   — no LP change, no new cache column. Populate `DispatchResult.emissions` from the same
   product at solve time so the declared field stops being a null (the `run_full_horizon`
   reconstruction then reads it, byte-identical). Optional: an hourly `co2_<year>.parquet`
   sidecar under the run's `hourly/`, gated by a reporting flag, default off.
2. **Import-attributed line** (reported only): per year, Σ import-tranche MWh × tranche EF
   (`IMPORT_TRANCHE_EF`, CARB unspecified 0.428 t/MWh for the WECC unspecified block, 0 for
   firm hydro / HQ), written as `import_co2_mt_reported` beside `emissions_mt`, never
   inside it, with the disclosure string baked into the summary.
3. **Unserved energy line.** `unserved_mwh` per year from the slack column, beside CO2.
4. **Multi-metric matrix frame + deltas.** `build_matrix_frame` carries every scalar in
   `_summarize_year` plus `unserved_mwh`; a new `scripts/report_scenario_deltas.py`
   (generalized from `report_ces_campaign.py`, keyed on a `--reference-case`, not a
   premium) emits per ISO: capacity/generation/CO2 by fuel deltas vs REF per year,
   cumulative CO2 delta, evolution-ledger deltas (builds/retirements/retrofits), captured
   prices, curtailment. `report_ces_campaign.py` keeps its premium-specific tables and
   delegates the generic ones.
5. **Six-ISO rollup.** `scripts/collate_scenario_campaign.py`: reads every
   `results/<campaign>/<iso>/<case>/full_horizon_summary.json`, sums `emissions_mt` across
   the ISOs present, reports the three side lines, refuses to label the sum "national"
   (label: "six-ISO modeled system"), and writes the campaign-level delta table.
6. **Scenario YAML set.** One base forecast YAML per ISO (`<iso>_scenario_base_2026_2050.yaml`
   and `_2026_2030.yaml` for the T1 window), varying nothing but ISO and horizon, plus
   `configs/scenario_campaign_matrix.yaml` in `cases:` mode carrying the §3.5 case set with
   every case a one-line field override. A generic `--set field=value` override on
   `run_full_horizon.py` and `run_ces_leg.py` (validated against `ScenarioConfig` field
   names; recorded in `run_config.json`) so a probe never needs a throwaway file.
7. **Registration.** A `scenario` kind for `register_forecast_run.py --summary` carrying
   `campaign`, `case`, `reference_case` in meta; the run explorer groups by campaign and
   shows the delta-vs-REF sparkline for CO2 alongside the level.
8. **Tests.** Trivial-first (rule "Testing Pattern"): a 1-gen/1-zone/24-h fixture where
   by-fuel and by-zone CO2 sum to `emissions_mt` exactly; the import line excluded from the
   total; delta table reproduces hand arithmetic on two synthetic summaries.

Exit: a paired T0 (NEISO 2026, REF vs `carbon_price_delta=25`) reported through the new
tables with by-class CO2 deltas, the import line, and the rollup script consuming one ISO.

### WS-1 — Carbon price `[FABLE]` (semantics + seams) then `[OPUS]` (six-ISO probe)

Owned files: `policy/carbon.py`, `policy/cap_and_trade.py`, `config/scenario_resolvers.py`,
`model/interchange/spec.py` (one line), `runner.py` (the `assemble_mc` call site), tests,
`configs/scenario_campaign_matrix.yaml` (carbon cases), the six matrix shards.

1. **Federal-price semantics (G-C1; owner box D-1).** Replace the forecast branch at
   `cap_and_trade.py:289-291` so an explicit non-`zero` `carbon_price_path` becomes a
   **floor**: `effective = max(RFF path(year), program trajectory(year))` on a program ISO
   (the path alone elsewhere). Rationale: a federal economy-wide price coexists with state
   programs, which may exceed it; under it a state cap's allowance price cannot fall below
   the federal price as a binding cost to the unit. `carbon_price` (scalar) keeps its Q26
   replace + guard semantics untouched. Update the one test asserting "explicit RFF path
   wins" (`test_cap_and_trade.py:135`) to assert the floor; add the mirror test that NEISO
   `tight` is a strict increase in every horizon year. Extend the D34 guard to fire on the
   path branch too. Cache-epoch ledger entry (`results/cache.py`) — no committed forecast
   bundle carries a non-zero path on a program ISO, so nothing stale is created. Re-read
   the `tight` / `rollback` bundle definitions against the repaired semantics and record
   the resolved per-ISO carbon trajectory for each bundle in the finding.
2. **Seam defects.** G-C2: `spec.py:1931` → `resolve_carbon_price(config, year)`
   (reproduce with a CAISO T0 that the WECC unspecified block's offer moves by
   `0.428 × price`). G-C3: build the membership-weighted column in `runner.py` exactly as
   `run_calibration.py:4022-4052` does, gated identically, so PJM's partial footprint is
   right the day a PJM forecast carbon price is non-zero; assert byte-identity for every
   uniform-membership ISO.
3. **Cap-and-trade alternative.** Pre-declare (do not run) the mass-cap arm: one case
   `CAP-RGGI-TIGHT` (a declining `mass_cap_tons` schedule on the program ISOs) so the
   price-vs-quantity comparison is a config, not a build. Verify the cap row's slack
   diagnostic is exported (G-E4 rider).
4. **Six-ISO paired probe (T0, 2026 only, one solve-year per arm).** REF vs
   `carbon_price_path="mid"` (post-repair) in every ISO; score P1-style: CO2 falls,
   load-weighted price rises by ≈ `Δcarbon × marginal-unit rate` in the hours a fossil unit
   is marginal, coal→gas re-ordering visible in by-class CO2, footprint confined to
   fossil rows. **STOP gate, structural only** (rule 29). Register as `scenario` probes.
5. **T1-F ladder where cheap.** NEISO and ERCOT 2026–2030, `CARB-LO / MID / HI` (RFF
   low/mid/high as floors) + REF: first deployment response (CCS retrofit screen, thermal
   entry mix, VRE/storage entry through prices); invariants I1–I14; delta tables. NEISO's
   result is quotable at horizon under its open gate (§3.5).
6. Matrix: cells for `carbon_price_path` (post-repair semantics) in all six shards with the
   probe evidence; `mass_cap_enabled` stays `U` until run.

Exit: floor semantics landed with byte-identity for every keeper and every zero-path
forecast bundle; both seam defects closed with tests; six paired probes registered and
right-signed; a NEISO+ERCOT T1-F carbon ladder on the dashboard with by-class CO2 deltas.

### WS-2 — National clean energy standard `[FABLE]` (row) + `[OPUS]` (ladder + clearing)

Owned files: `model/lp/rows.py` (a new row builder, or the clean-tier builder generalized),
`policy/federal_ces.py`, `policy/clean_tiers.py` (the region coupling), `runner.py`
(arming + dual plumbing), `scenarios.py` (≤ 3 fields), a new
`scripts/ces_national_clearing.py`, `configs/ces_*`, tests, the six shards.

1. **Endogenous CES target row (G-S1, G-S3; the CES plan's Wave 5).** One annual row per
   ISO: `Σ_columns credit_fraction[c] · gen[c,t] + escape ≥ target(year) · Σ demand`, where
   `credit_fraction` is the existing `federal_ces.unit_credit_fractions` (so `clean_capture`
   and `cesa_ci` both work unchanged: wind/solar zone columns 1.0, nuclear/hydro/geothermal
   generator columns 1.0, CCS 0.95, unabated 0), the escape column priced at an
   alternative-compliance ceiling, and the dual the endogenous federal EAC price. Build it
   on the clean-tier row machinery (it already admits nuclear and prices an escape,
   `rows.py:145-202`) as a **federal region spanning all load zones**, relaxing the
   "requires the RPS region family" coupling (`rows.py:1346`) so it can stand alone or
   beside the state rows. Vectorized (rule 2); one row per year, so LP size is untouched.
   Dual → `clean_attribute_price_by_fuel` → entry/retirement through the existing
   `max()` (no new consumer). Fields: `federal_ces_target_by_year: dict[int,float] | None`
   (sparse knots, linear between, `None` = no row), `federal_ces_acp_usd_per_mwh` (the
   escape price), and a mode guard that the row and a non-zero *exogenous* premium are
   mutually exclusive in one config (one mechanism per phenomenon, rule 19). Forecast-only,
   coerced inert in backcast, cache-optional at `None`.
2. **Interaction with state RPS.** Document and test the three postures: state rows +
   federal row both live (default — the state REC and federal EAC are separate attributes
   and the entry screen takes the max, matching the no-stack doctrine);
   `federal_ces_replaces_state_rps=True` (pure federal); state rows only (REF).
3. **National clearing post-processor (G-S2).** `scripts/ces_national_clearing.py`: given
   the premium-ladder legs for every ISO in a campaign, interpolate each ISO's
   clean-share-vs-premium curve, find the **uniform premium** at which
   Σ_ISO credited MWh ≥ national target × Σ_ISO load for each year, and report the per-ISO
   clean shares at that premium beside the per-ISO-target-row result. The two numbers
   bracket the cross-ISO-trade question; the memo reports both and the spread. Zero-solve;
   consumes committed legs.
4. **Re-prove the premium ladder at HEAD posture (G-S5).** Re-run the FF-3B POC
   (ERCOT 2026–2030, BAU + CES-20 + CES-40) at the current defaults (retirement rule,
   fossil dated exits, CCS capex scaling, entry dampers — every flip since July moved it)
   and register it; then NEISO 2026–2030 the same, so a program-ISO with RGGI armed is on
   record. Compare against the July surface in the finding — the direction must hold; the
   level will not, and the finding says why per flip.
5. **Target-row probe.** NEISO 2026 T0: REF vs `federal_ces_target_by_year={2026: 0.55,
   2035: 0.80, 2050: 1.0}` (illustrative; the campaign target is owner box D-2). Structural
   gate: the row binds or its escape fires, the dual equals the escape price when it fires,
   credited share ≥ target when it does not, CO2 falls, the footprint is the eligible
   columns only.
6. Matrix: row + six cells for the target-row field; `federal_ces_enabled` cells
   re-stamped with the HEAD-posture ladder evidence.

Exit: a national CES is expressible **two ways** in a committed matrix (`CES-P10/20/30`
premium legs and `CES-T80` target legs), both wired to dispatch and deployment, both probed
right-signed, and the clearing script produces the uniform-price answer from the legs.

### WS-3 — Voluntary clean energy demand `[FABLE]` (design memo → build) + `[OPUS]` (probe)

Owned files: new `policy/voluntary_demand.py`, `model/lp/rows.py` (row family reuse),
`data/datacenter.py` (the DC-linked volume construction), `constants.py` (public anchors),
`scenarios.py` (≤ 3 fields), tests, the six shards. Gated on owner box **D-3**.

1. **Design memo first** (the FF-0C / FF-G4 memo-first pattern, no code): representation,
   anchors, and the admissibility argument written out for the owner. The plan's
   recommendation:
   - **Representation: an annual volumetric clean-attribute demand row** — the RPS row's
     form with three differences: the RHS is a **volume** (MWh of voluntary demand in that
     ISO-year), not a share of total load; eligibility is the voluntary market's
     (wind, solar, geothermal, and — decision — nuclear/CCS for "carbon-free" programs);
     and the escape column is priced at a **willingness-to-pay ceiling** (the price at which
     the buyer forgoes the attribute), not a statutory ACP. The dual is the voluntary REC /
     PPA attribute price; it reaches the entry screen through the existing `max(EAC, RPS,
     clean)` seam, so a builder sees the higher of compliance and voluntary value — the
     no-stack rule holds (one attribute, one claim). No additionality mask in dispatch
     (the LP's wind/solar columns are zone aggregates with no vintage; annual REC matching
     has none either); additionality enters, if the owner wants it, only as an entry-screen
     rule (voluntary value credited to new builds only).
   - **Volume construction, DC-linked:** `voluntary_mwh(ISO, y) = baseline_share(ISO) ×
     non-DC load(y) + committed_fraction(y) × DC block energy(ISO, y)`. The DC half rides the
     existing `datacenter_load_path` block (the hyperscalers' published 100 %-clean /
     24/7 commitments are the reason voluntary demand is growing), so a high-DC case and a
     high-voluntary case are coherent by construction. Levels via one axis
     `voluntary_clean_demand_path: off/low/mid/high`, forecast-only, `off` byte-identical.
   - **Public anchors (rule 13 reproducibility, no proprietary series):** NREL's annual
     *Status and Trends in the U.S. Voluntary Green Power Market* (national volumes by
     product — PPAs, utility green pricing, unbundled RECs, CCAs; public data tables) for
     the baseline share; the CEBA deal tracker's public aggregate for the PPA trend; the
     hyperscalers' published commitments (Google 24/7 CFE by 2030, Microsoft 100/100/0,
     Amazon and Meta 100 % renewable matching) for `committed_fraction`; ISO allocation of
     the non-DC baseline by commercial-sector load share (EIA-861, already the RPS
     compliance-region basis in `capacity_market.py:4625-4656`). Every number lands in
     `constants.py` with the citation; the memo lists which cells are sourced and which
     are `needs-citation` so the owner sees the provenance before a solve.
   - **Hourly (24/7) matching — deferred, with the reason.** An hourly-matched variant is a
     `T`-row block per buyer (feasible vectorized, but it changes the dispatch LP's shape
     and adds a buyer-portfolio problem the isolated `scope2-lce-portfolio/` tool already
     solves on the simulator's LMPs). Recommendation: keep 24/7 in that tool (feed it the
     scenario LMPs) and reserve an in-LP hourly row for a later owner box (D-3b).
2. **Build** per the memo's signed boxes: row family reuse, resolver, config fields
   (`voluntary_clean_demand_path`, `voluntary_wtp_ceiling_usd_per_mwh`,
   `voluntary_eligible_fuels`), inert-in-backcast coercion, cache-optional at `off`,
   matrix row + six cells, tests (trivial 1-gen/24-h binding case: dual = the clean-minus-
   dirty cost gap; ceiling case: dual = WTP, escape MWh = shortfall).
3. **Probe.** ERCOT 2026 T0 (the ISO with the largest DC block and the thinnest RPS —
   the voluntary row is the *only* attribute driver there): REF vs `mid`. Structural gate:
   the row binds, the dual is positive and below the ceiling, curtailment falls before
   dispatch changes (clean MWh that was dumped is the first thing a REC buyer pays for),
   CO2 falls, thermal rows are the only displaced footprint. Then T1-F 2026–2030 to see the
   first entry-wave response (the mechanism's deployment half).

Exit: voluntary demand is a registered forecast-only axis with public anchors, wired to
dispatch and deployment through existing seams, probed right-signed on ERCOT, and the
24/7 question is filed with a recommendation rather than left implicit.

### WS-4 — High load growth `[OPUS]` (coherence + posture) with one `[FABLE]` adjudication

Owned files: `constants.py` (DC zone shares, growth tables), `data/datacenter.py`,
`config/scenario_resolvers.py` (a coherent-case helper), `configs/scenario_campaign_matrix.yaml`
(load cases), optionally a `load-forecast` curated datatype (owner-gated), tests, shards.

1. **Declare the high case (G-L3).** `LOAD-HI` = `demand_growth_path="high"` +
   `datacenter_load_path="high"` + `electrification_path` as-is (off, or `mid` for NEISO
   where the layer is sourced) — written as a *named case*, with the ERCOT tail-regime
   arithmetic (`datacenter.py:318-320`) disclosed in the case comment. Add `LOAD-HI-ORGANIC`
   (growth high, DC mid) as the attribution companion so the DC block's share of the
   emissions delta is readable.
2. **DC siting currency.** `DATACENTER_ZONE_SHARE` for ERCOT and MISO from published
   large-load queue geography (ERCOT LFL officer updates by zone; MISO LTLF DC
   decomposition), replacing the `load_share` fallback; NEISO `DATACENTER_ADDITIONS_MW`
   stays `{}` with its immateriality note re-checked against the 2026 CELT.
3. **Adequacy posture under high load — a `[FABLE]` adjudication, no tuning.** Pre-declare
   how each ISO's high case is *read*: curve-ON ISOs (PJM/MISO/NYISO/NEISO/CAISO) meet load
   with the backstop and the entry ladder (`entry_rate_limits`), so the emissions delta
   includes the backstop gas_ct — reported separately as "backstop-built"; ERCOT
   (energy-only, no backstop) meets it with scarcity-priced entry or **does not meet it**,
   and the unserved energy is reported beside CO2. The invariant to watch is I12/I3 —
   FAILs that already exist at `mid` (§2.4) will widen; the plan does not charter fixing
   them (capx queue), it charters *disclosing* them per case.
4. **Optional published-forecast intake (G-L2; owner box D-4).** A curated `load-forecast`
   datatype through the data-intake skill: per ISO, the published low/mid/high energy and
   peak cases with the DC decomposition (ERCOT LTLF, PJM LTLF Table B-9b, NYISO Gold Book
   Table I-1a, ISO-NE CELT, CEC IEPR, MISO LTLF), replacing the hand constants and giving
   the electrification layers their missing cells. Provenance upgrade only — the scenario
   runs on the cited constants without it.
5. **Probe.** Every ISO T0 2026 REF vs `LOAD-HI` (load is live in year one): CO2 rises
   with load at roughly the fossil average rate in the hours the added load is served by
   fossil, unserved energy reported, price rises. Then NEISO + ERCOT T1-F 2026–2030 for the
   deployment response (backstop / entry / retirement deferral).

Exit: the high-load case is one named, coherent, disclosed config per ISO; siting is
sourced where the block is material; the adequacy reading is pre-declared; probes
registered.

### WS-5 — Campaign execution and the emissions synthesis (gated per ISO)

The campaign is the §3.5 case set solved per ISO at the widest window the ISO's §2.1b gate
allows, then differenced and rolled up by WS-0's tooling. **Every full-horizon leg needs
the per-campaign owner authorization (leg d) even for NEISO** — Q13/Q25 were "this
campaign only" and GOLDEN-3 is D60's; a scenario campaign is a new grant (§6 D-5).

Staging (rule 29, FF plan §2.4):

1. **Stage A — T1-F everywhere (≤ 5 solve-years, no gate needed).** All six ISOs ×
   the case set × 2026–2030. Measured per-year anchors: ERCOT ~2.4 min, NEISO ~1.5, PJM
   ~5.6 (2026–2030), MISO ~10–13, CAISO ~8, NYISO ~4 (D46/D60 measurements; the board's
   earlier 7–10× over-estimates are retired). A 12-case set is ≈ 2.5 h ERCOT, 1.5 h NEISO,
   6 h PJM, 12 h MISO, 8 h CAISO, 4 h NYISO of serial LP — schedulable in one to two days
   at ≤ 2 concurrent invocations (one when MISO or PJM runs). Deliverable: dispatch
   response + first entry wave, by-class CO2 deltas, six-ISO rollup for 2026–2030.
2. **Stage B — full horizon where the gate is open.** NEISO now (with the D-5 grant);
   NYISO when its `complete` marker is back and Q45's grant is re-confirmed for this
   campaign; ERCOT / PJM when leg (b) clears; CAISO / MISO after (a)+(b). Reuse the REF
   golden where one exists (NEISO GOLDEN-3 at the campaign HEAD) — never re-solve REF.
   Measured full-horizon cost: NEISO 29 min per case (GOLDEN-1), so a 12-case NEISO
   campaign is ≈ 6 h serial; CAISO ≈ 3 h per case; PJM > 8 h per case (two per-plant ISOs
   never co-run past 2035).
3. **Stage C — the synthesis memo** (`docs/handoffs/FINDING-scenario-campaign-<date>.md`):
   per mechanism, per ISO, per horizon: the dispatch delta (2026), the deployment delta
   (builds/retirements/retrofits to the horizon reached), CO2 delta per year and
   cumulative, the six-ISO sum with its three side lines, the combined-case interactions
   (§3.5), and the honest-unfit list (which ISOs are T1-only and why, which invariants
   fail in which case, the import boundary, the missing regions). Registered on the
   forecast dashboard under one campaign id; the FC-6 paired battery re-run so the
   campaign's own pairs are on the rubric record.

### 3.5 The case set (levels COMMITTED per S3, 2026-09-06)

**THE LEVELS IN THIS TABLE ARE COMMITTED, NOT ILLUSTRATIVE.** Owner card D-2 was ruled
**2026-09-06 as S3: this table is the COMMITTED default** (SCN-DESK r#5 amendment 1; §6
and `docs/handoffs/scenario-desk-ledger-2026-09.md` §2). **No number moved and no re-solve
was owed** — every level the building lanes carried under an "illustrative" label is the
level S3 committed, so the ruling changed the label and not the number
(`docs/handoffs/FINDING-scn-levels-2026-09-06.md`, SCN-LEVELS 2026-09-06).

`configs/scenario_campaign_matrix.yaml`, `cases:` mode, every case one or two field
overrides on REF.

**Three levels in this table S3 did NOT reach**, because the table is silent on them, and
none may be inferred from the ruling: (i) `CAP-STATE-TIGHT`'s declining budget — the row
writes "declining `mass_cap_tons`" with no number, so the slope stays the OWNER level
SCN-WS1a labelled it (`FINDING-scn-ws1a-2026-09-05.md` §4.2); (ii) two voluntary sub-cells
— S3 commits "the WS-3a memo's box-5 defaults", and box 5 itself leaves `f_commit` mid and
the WTP-ceiling *level* owner-set; (iii) the carbon ladder's **form** — the committed level
is the RFF **path** ladder, but G-C1 makes a path a carbon *cut* on CAISO/NYISO/NEISO until
**SCN-WS1c** lands S2's floor, so the campaign runs the reduced additive `carbon_price_delta`
form in the interim and its knots {15, 25, 50} are a desk stand-in, not ruled levels.
Cards **D-3c** (voluntary eligible set) and **D-6** (attribute netting) also remain open.

| Case | Overrides | Question it answers |
|---|---|---|
| `REF` | — | the reference; the ISO's shipped posture |
| `CARB-LO` / `CARB-MID` / `CARB-HI` | `carbon_price_path: low/mid/high` (floor semantics after WS-1) | price → dispatch re-ordering, CCS, thermal mix, VRE entry via prices, CO2 |
| `CAP-STATE-TIGHT` | `mass_cap_enabled: true` + declining `mass_cap_tons` on program ISOs | price vs quantity instrument comparison |
| `CES-P10` / `CES-P20` / `CES-P30` | `federal_ces_enabled: true`, `federal_ces_premium_usd_per_mwh: 10/20/30` | the uniform-price (tradeable) CES response curve |
| `CES-T80` | `federal_ces_target_by_year: {2026: 0.55, 2035: 0.80, 2050: 1.00}`, `federal_ces_acp_usd_per_mwh: 50.0` — **committed, S3**; `<current>` = 0.55 per §3 WS-2 item 5, the value SCN-WS2a probed. **LIVE** in the campaign YAML since 2026-09-06 | the uniform-share (no-trade) standard; dual = implied EAC price |
| `VOL-MID` / `VOL-HI` | `voluntary_clean_demand_path: mid/high` | voluntary buyers → curtailment, entry, CO2 |
| `LOAD-HI` / `LOAD-HI-ORGANIC` | `demand_growth_path: high` + `datacenter_load_path: high` / `mid` | load → adequacy, backstop, CO2 per MWh |
| `CARB-MID+LOAD-HI` | both | does a carbon price hold CO2 flat under DC growth? |
| `CES-P20+VOL-HI` | both | attribute double-claim test: voluntary demand counts toward (or is netted from) the standard — reported both ways |
| `ALL-CLEAN` | CARB-MID + CES-T80 + VOL-HI + LOAD-HI | the coherent policy corner under high load |

Twelve to fourteen cases; the two corners of the existing `configs/scenario_matrix.yaml`
(`CORNER-HI-EMIT` / `CORNER-LO-EMIT`) remain the envelope reference and are not re-solved.

---

## 4. Cross-cutting constraints and caveats the campaign must carry

- **Per-ISO solves, no cross-ISO trade.** Six independent LPs; a national instrument is
  represented either as a uniform price or a uniform share (§3.2). Inter-ISO flows are the
  fixed import nodes (CAISO WECC, NEISO HQ) and nothing else; a carbon price does not
  re-route power between PJM and MISO in this model. Stated in every memo.
- **Emissions boundary.** In-ISO attributional CO2; imports reported beside, not inside;
  the six ISOs are not the United States. No marginal emission rates (G-E6). Startup and
  partial-load emissions are not in the LP rate (`model-audit-2026-06.md:75`).
- **Deployment credibility is ISO-specific and already measured.** The T1-F rubric holds
  ERCOT / CAISO / PJM / MISO on adequacy invariants (I7/I12/I3) and CAISO on a 65.5 %
  backstop share; ERCOT solar entry is zero in hindcast (R1); the storage entry stack is
  arbitrage-short in every year (D36). A scenario's *deployment* delta in those ISOs is
  a delta between two runs that share the defect — directionally informative, not a
  forecast of GW. The synthesis memo grades each ISO's deployment response by its live
  FC map and never quotes a HOLD ISO's 2050 mix as a result.
- **Rules that bind every session here:** 1 `[R-STRUCT]` (no mechanism judged by its
  residual; scenario responses are never "tuned" to look right), 5/24 (every lever
  registered and cited), 13/14 (public, reproducible anchors; accurate data over
  estimates), 19 (one mechanism per phenomenon — the attribute rows compose through
  `max()`, never sum), 22 (2026+ forecast runs are unrestricted; no H1-2026 actuals
  anywhere), 25 (no ISO's fitted value crosses into another — voluntary and DC anchors are
  per-ISO), 26 (deleted means deleted — no zeroed legacy knobs), 27 (`[R-PUSH]`; Opus or
  Fable only), 28 (matrix duty in the same PR), 29 (one-year screen, structural STOP gate,
  keeper as control). §2.1b window cap and per-campaign grant. No CI solves.
- **Attribute double-claiming.** A MWh can carry one attribute claim. When a federal CES,
  a state RPS and a voluntary buyer coexist, the model's `max()` composition gives the
  builder the highest single value (correct for entry) but the *dispatch* rows are
  independent constraints and could each count the same MWh. WS-2/WS-3 must state the
  netting rule (voluntary demand counts toward the standard, or is netted from it) and
  the campaign reports the `CES-P20+VOL-HI` interaction both ways.

---

## 5. Sequencing, dependencies, effort

```
WS-0 foundation ──────────────┬──────────────────────────────┐
  (1 Opus session, ~1 day,    │                              │
   zero-solve + T0)           │                              │
WS-1 carbon: [FABLE] repair ──┤  [OPUS] six-ISO T0 probe ────┤
  (1 + 1 sessions)            │  + NEISO/ERCOT T1-F ladder   │
WS-2 CES: [FABLE] target row ─┤  [OPUS] ladder re-prove +    │
  (1 + 1 sessions)            │  clearing script + probes    │
WS-3 voluntary: [FABLE] memo ─┼─ owner D-3 ─→ [FABLE] build ─┤ [OPUS] probes
  (1 + 1 + 1 sessions)        │                              │
WS-4 load: [OPUS] coherence ──┤  [FABLE] adequacy reading ───┤
  (1 + 1 sessions)            │                              │
                              └──→ WS-5 Stage A (T1-F, all ISOs) ──→ Stage B (gated) ──→ Stage C memo
```

- WS-0 first; WS-1…WS-4 in parallel after it (file ownership is disjoint by construction:
  carbon touches the carbon resolver and one interchange line; CES touches the LP row
  family and `federal_ces.py`; voluntary adds a module and reuses the row family **after**
  WS-2's coupling change merges — the one ordering constraint; load touches constants and
  the DC module).
- Session count: ≈ 12 build/probe sessions + Stage A (≈ 2 days of in-session LP across
  the six ISOs at ≤ 2 concurrent) + Stage B per gate-open ISO + 1 synthesis session.
- What this plan does **not** charter: closing the T1-F adequacy blockers (I7/I12/I3),
  the ERCOT solar-entry residual, the storage arbitrage gap, curve-ON over-fire — all in
  the capx director's queue. This plan's readiness is orthogonal to them; the campaign's
  *credibility* per ISO is not, and §4 says how that is disclosed.

### 5.1 Readiness scorecard (maintained by each landing session)

| Criterion (§1) | Carbon | CES premium | CES target | Voluntary | Load-HI | Emissions |
|---|---|---|---|---|---|---|
| 1 expressible in committed config | yes — **G-C1 CLOSED** (SCN-WS1c 2026-09-06, executing owner ruling **S2**/card D-1): `resolved = max(RFF path, program trajectory)` on a program ISO, the path alone elsewhere. The `tight` cut of $16–$102/t on CAISO/NYISO/NEISO is gone — corrected +$15.98 to +$102.29/t in all 25 yrs, and **no cell anywhere falls**. Gates: 450/450 cells match WS-1a's committed `floor` prediction; footprint exactly 3×25 cells; 0 of 90 committed run_configs on the changed branch and 0 keys moved. **`tight` is now an exact NO-OP on the three program ISOs** — the ruled outcome; **D-1(b)** (what `tight` should mean there) and **D-1(c)** (PJM's partial footprint) stay OPEN. `FINDING-scn-ws1c-2026-09-06.md` | yes | **yes** (SCN-WS2a: `federal_ces_target_by_year` + `federal_ces_acp_usd_per_mwh`; illustrative level, D-2 open) | **yes** (SCN-WS3b 2026-09-06, executing owner ruling **S1**/card D-3): `voluntary_clean_demand_path` off/low/mid/high + `voluntary_wtp_ceiling_usd_per_mwh` + `voluntary_eligible_fuels`, all forecast-only (the whole block coerced to its defaults in backcast/hindcast) and cache-optional at `off`; levels in `constants.VOLUNTARY_*` with citations (the NREL 2021/2022/2023 national voluntary share series 0.06/0.06/0.08; the cited $2–7/MWh public REC range; `f_commit` low 0 / high 1.0). `VOL-MID` / `VOL-HI` / `CES-P20+VOL-HI` / `ALL-CLEAN` are LIVE in `configs/scenario_campaign_matrix.yaml` and **HELD under S5** (Stage A-POLICY). Two cells stay LABELLED ILLUSTRATIVE and are re-presented (`f_commit` mid 0.5, WTP mid $4.5 — unreached by S3); `w_ISO` is `needs-intake` (EIA-861 commercial share, resolves to 1.0); the eligible-set default is the memo's RECOMMENDATION (D-3c OPEN); no netting logic is built (D-6 OPEN). `FINDING-scn-ws3b-2026-09-06.md` | **yes** — named cases `LOAD-HI` / `LOAD-HI-ORGANIC` live in `configs/scenario_campaign_matrix.yaml` with the ERCOT tail-regime arithmetic and the six-ISO adequacy reading pre-declared in the case comment (SCN-WS4b 2026-09-06, `FINDING-scn-ws4b-2026-09-06.md` §2, `load-hi-adequacy-reading-2026-09-06.md`); siting sourced for ERCOT/PJM/MISO (SCN-WS4a). **Inputs re-derived 2026-09-06 (SCN-LOAD, ruling S4)**: the growth, DC and electrification constants now come from the curated `load-forecast` datatype rather than hand transcription — ERCOT's low/mid/high are its own published `base_economic` / Adjusted / TSP-Provided cases, so the growth and DC axes are coherent by construction; CAISO's `high := mid`, MISO's extrapolated `high` and MISO/NYISO's `low := 0` all close on published tables; the electrification row goes 1 armed cell → 3. **Two consequences for this case**: demand at 2030 moves +30.9 % (ERCOT mid) to +17.8 % (PJM mid), and the ERCOT tail-regime arithmetic in the `LOAD-HI` case comment is **stale** — the block's 2030 share of grown energy on the high path falls 97.3 % → 44.1 % (`FINDING-scn-load-2026-09-06.md` §4.1, routed) | — |
| 2 reaches dispatch + deployment | yes (G-C2 + G-C3 closed at WS-1a; cap-row dual NOT exported — G-E4 rider to WS-0) | yes | **yes** (SCN-WS2a: the row → dispatch; dual → the existing `max()` screen seam; deployment leg not exercised by the 1-yr T0) | **yes** (SCN-WS3b): the row rides the clean-tier family as its second consumer (region order state → federal → voluntary, all-zone mask, RHS = `V / E_total` of every zone's demand, escape at the WTP ceiling) → dispatch; its dual → the existing `clean_attribute_price_by_fuel → max(EAC, RPS dual, clean dual)` screen seam, no new consumer. Trivial-first LP (1 zone / 24 h): binding dual = the clean-minus-dirty gap; ceiling dual = WTP with escape = the shortfall (objective identity); curtailed wind recovered before thermal is displaced. Deployment leg not exercised — a zero-LP build lane | yes | — |
| 3 paired probe right-signed, per ISO | **ALL SIX ISOs measured at 2027 on the S2 floor (SCN-WS1b-r2, 2026-09-06, `FINDING-scn-ws1b-2026-09-06.md`)** — twelve paired T0 arms, REF vs `carbon_price_path=mid`. **Three LIVE** (ERCOT/PJM/MISO, +$3.75/t): right-signed, STOP gate **8/8 PASS on PJM and MISO**, 7 PASS + 1 reported band miss on ERCOT; coal→gas re-ordering visible in all three, with PJM shedding **17.4 TWh of coal (7.7 % of its coal output)** to a $3.75/t price because the coal/gas-CC spread is narrow, not because the price is large. **Three INERT** (CAISO/NYISO/NEISO): Δ = **0.000000** on every metric to six decimals — the ruled S2 outcome measured, not a null. **CAMPAIGN-GRADE ON PRICE: PJM and MISO only.** ERCOT's price level is NOT (641 scarcity hours, reserve margin −6.5 %, 4.6 TWh unserved in BOTH arms — the known G-S4 defect); its CO2 and merit-order results are robust to it, its price is not. **Note the charter's 2026-only leg was structurally unrunnable** — `CARBON_PRICE_PATHS` anchors every RFF path at $0 in 2026, caught at zero LP by phase 0 and re-scoped to 2027 (desk r#7 ratified). **Cross-campaign result:** the price-setting marginal rate exceeds SCN-WS4c's load-following rate in 3/3 ISOs (1.13–1.33×), so the two are not interchangeable; the magnitude is a range, not a constant, and coal share does not order it **ERCOT Stage A-POLICY (SCN-WS5A-POLICY-ERCOT, 2026-09-07, `FINDING-scn-ws5a-policy-ercot-2026-09-06.md`): CARB-LO/MID/HI at T1-F 2026–2030 at THE PIN. 2027 (control valid): ΔCO2 −0.393 / −0.928 / −2.335 Mt at $2.00 / $3.75 / $7.50/t, coal→gas-CC ~1:1, every zero-carbon row 0.0000, import 0.0 by construction (upper bound); CARB-MID 2027 reproduces WS-1b to every digit (255.0452 Mt); dose-response SUPER-linear (HI 2.52× MID). Leg-vs-leg at the pin the response SATURATES under scarcity (HI − LO −1.94 → −0.13 Mt, 2027 → 2030). **2028–2030 vs REF is CONTAMINATED**: every arm converts ~3 GW/yr of gas-CC to CCS at the retrofit cap (VOL-HI at carbon $0 included) while the `1cc45bb2` REF converts none — capx D65-B is LIVE on ERCOT; the REF/LOAD-HI re-solve is routed. Price disclosure-only (G2). Gates 12 PASS / 0 kill.** **NEISO (SCN-WS5A-POLICY-NEISO, 2026-09-07, `FINDING-scn-ws5a-policy-neiso-2026-09-07.md`): the S2 inertness EXTENDS FROM WS-1b's single 2027 probe TO THE WHOLE T1-F WINDOW, and it is now a phase-0 KILL rather than a solved null.** All three `CARB-*` cases differ from REF in exactly one resolved field, `carbon_price_path`, whose only LP-affecting consumer is `resolved_base_trajectory_price`'s `max` (`carbon.py:187`, census at the pin); NEISO's projected RGGI trajectory 26.0545 / 27.8783 / 29.8298 / 31.9179 / 34.1521 $/t dominates every registered path in every year (closest approach `high` at 2030, $30.00 vs $34.15). **20 solve-years never spent.** `CARB-MID+LOAD-HI` is killed on the same identity against the **committed** `LOAD-HI` leg (key `0d5c394b6c4e5cb6`), so the campaign's one combined carbon+load case contributes nothing on NEISO beyond what the load lane published. | **ERCOT + NEISO at HEAD posture (SCN-WS2b)** — direction holds table by table vs the July surface, invariant pattern identical; ERCOT saturates above ~$20/MWh on the queue budget and its price/deployment levels are not campaign-grade (adequacy collapse, G-S4 stands); NEISO right-signed on share/price/imports but its CO2 read-out is governed by the CCS emission-rate seam (`FINDING-scn-ws2b-2026-09-06.md` §5.3, routed) **ERCOT (SCN-WS5A-POLICY-ERCOT, 2026-09-07, `FINDING-scn-ws5a-policy-ercot-2026-09-06.md`): CES-P10/P20/P30 at the pin. No dispatch footprint in 2026–2027 (every fuel row 0.0000); the premium acts through the offer (negative-price hours 522 → 599, captured wind −$0.9 / −$1.8) and the ENTRY screen: P20 +2,000 MW wind for solar (2030), P30 +1,500 MW solar / −1,000 MW gas-CC (2029) + 5,000 MW wind (2030). **The ladder does NOT saturate at $20–30** at the pin (clean 0.3992 vs 0.4058, CO2 303.08 vs 299.59 Mt) — WS-2b's `iso_budget_exhausted` saturation was its POC base's. 2028–2030 vs REF contaminated by the D65-B CCS conversion (routed).** **NEISO ladder RE-RUN AT THE POLICY PIN (SCN-WS5A-POLICY-NEISO, 2026-09-07): the response is LARGE, ENTIRELY RETROFIT-DRIVEN, AND DOES NOT SATURATE — and it REVERSES SIGN on the leakage line.** 2030 in-ISO CO2 6.1058 (REF) → 3.0942 / 2.8713 / 2.9392 Mt at $10 / $20 / $30, i.e. **non-monotone at the top rung**, while the leakage-inclusive total is strictly monotone 10.8715 → 6.9622 → 6.1017 → 5.2251 Mt: the extra premium pulls `gas_cc_ccs` in (25.93 → 62.57 TWh) and pushes imports out (`import_co2_mt_reported` 4.7657 → 2.2859). **A reader given `emissions_mt` alone would conclude a higher CES premium raises NEISO's emissions.** `vre_mw` is IDENTICAL to REF in every rung and every year, so WS-2b's July "adds ZERO economic entry" now has its mechanism: the premium is masked on the entry screen by NEISO's own $50/MWh RPS escape (`new_entry.py:1132-1143`, the RPS leg applied to every tech with no fuel gate) and reaches the ISO only through the retirement/CCS-retrofit screens, whose RPS leg IS fuel-gated to {wind, solar}. The July CO2 read-out caveat is RETIRED: this ran post-D77. | NEISO only, escape regime (dual = ACP $50 exactly; CO2 +2e-4 reported not smoothed — `FINDING-scn-ws2a-2026-09-05.md` §4.3). **Quotable as a CAMPAIGN-LEVEL result since S3** — it was run at exactly the committed level, so it is no longer only a machinery demonstration **ERCOT (SCN-WS5A-POLICY-ERCOT, 2026-09-07, `FINDING-scn-ws5a-policy-ercot-2026-09-06.md`): CES-T80 at the committed level. Escape regime in all five years, dual = ACP $50.0000 exactly (G4 exact); REF's credited share 0.3953 → 0.3172 never reaches 0.55. First deployment reading: the $50 dual swaps +3,500 MW solar for −3,000 MW gas-CC in 2029 and pays +16.8 / +16.4 TWh of unserved (2029/30). **DEFECT FOUND (routed): the row credits DUMPED energy** — curtailment goes to 0.000 the year the row binds with thermal/storage/unserved unchanged and I3 gaining a 2.15–2.41 % dump line; ~4.9 TWh/yr of phantom credit at ERCOT.** **NEISO at T1-F, BOTH LIMBS OF THE IDENTITY EXERCISED BY ONE ARM (SCN-WS5A-POLICY-NEISO, 2026-09-07, `CES-T80`):** dual = ACP **50.0000 exactly** in 2026/2027/2028 where the target is unmet, **−0.0** in 2029 where REF's own credited share clears it, and **strictly interior 4.2912** in 2030 — so the escape regime WS-2a could only show at a 1-year T0 is now paired with a binding one. Deployment leg still NOT exercised, and now for a measured reason rather than a horizon limit: entry is identical to REF in every year because the $50 ACP equals NEISO's $50 RPS escape, so `max(50, 50)` adds nothing. `ALL-CLEAN` reproduces the identity with the voluntary row live beside it. | **no** **ERCOT (SCN-WS5A-POLICY-ERCOT, 2026-09-07, `FINDING-scn-ws5a-policy-ercot-2026-09-06.md`): VOL-HI / CES-P20+VOL-HI / ALL-CLEAN at the pin (VOL-MID killed at phase 0, slack all five years). Dual 0 / 0 / 7.0 / 7.0 / 7.0 $/MWh exactly (slack while V < eligible, escape at the `high` ceiling from 2028; G7 exact), ALL-CLEAN [50, 7] all years; escape 24.5 / 59.0 / 100.8 TWh. Price and unserved byte-identical to REF in every year; the row moves NO build; under a $20 premium its dual is irrelevant to deployment (build ≡ CES-P20); on top of carbon + DC-high load it adds 0.0000 Mt. Both nettings reported (counts-toward headline). **Same dump-crediting defect as the CES target** (routed): the row's first act is to "recover" REF's whole 4.9 TWh curtailment into the dump column.** **NEISO (SCN-WS5A-POLICY-NEISO, 2026-09-07) — THE CLEANEST FORM OF THE INSTRUMENT ANY ISO CAN PRODUCE, AND IT MOVES NOTHING.** `E_DC` is exactly 0 on NEISO, so `f_commit` multiplies zero and `s_base` is 0.08 on both paths: `VOL-MID` and `VOL-HI` carry the **identical volume to the MWh**, making the pair a pure $4.50-vs-$7.00/MWh WTP-ceiling ladder with no volume confound. **Measured: byte-identical in every reported scalar, fuel and capacity column in all five years; the only difference anywhere is the dual.** The row BINDS 2026-2028 (V 8.4289/8.4917/8.5549 TWh vs an eligible fleet pinned at its CF ceiling, 6.9162) and is slack 2029-2030; dual = the arm's own ceiling exactly when binding, −0.0 exactly when slack; 2026 escape = 1.5127 TWh exactly. So NEISO is the ISO that can carry D-2(b)'s ceiling evidence — and the answer it gives is **"the ceiling cannot be discriminated here"**, because $4.50 and $7.00 both sit under the $50 RPS escape the screens read. G8 is VACUOUS here (REF curtailment is 0.0000 TWh by construction) and must not read as a pass NEISO never earned. | **yes — all six** (SCN-WS4c 2026-09-06, `FINDING-scn-ws4c-2026-09-06.md`): 15 T0 arms (2026) + 4 T1-F arms (2026–2030), campaign `scn-ws4-probe`. CO2 rises in every ISO on the fossil stack alone (ERCOT +13.687 / PJM +20.084 / MISO +8.992 / CAISO +2.544 / NYISO +1.637 / NEISO +0.812 Mt), price rises in all six, footprint confined to fossil + imports, `by_fuel["import"]` 0.0 everywhere. **The implied marginal rate carries a SIGNED error vs the fossil-fleet average** — below it wherever coal is inframarginal (0.73× / 0.77× / 0.65×), above it where not (1.05× / 1.05× / 1.17×) — so "fossil-average × added MWh" is biased high 23–35 % with coal and low 5–17 % without. SCN-WS4b's readings score 20 HIT / 3 SPLIT / 3 MISS **CAMPAIGN LANDED, then RE-SOLVED (SCN-WS5A-LOAD + SCN-WS5A-RESOLVE, 2026-09-06)** — `scn-campaign-load-2026-09-06`, **16 legs / 80 solve-years, all rc=0**, six ISOs × {REF, LOAD-HI[, LOAD-HI-ORGANIC]} over T1-F 2026–2030 (`FINDING-scn-ws5a-load-synthesis-2026-09-06.md` + six per-ISO FINDINGs). The campaign **FALSIFIED ruling S5's premise** that the load half carries no `gas_cc_ccs`: five of six ISOs carry mis-rated CCS in REF from 2028, which is card **D-10** and owner ruling **S8**. **13 of the 16 legs need a re-solve post-capx-D77; 7 are landed** (NEISO 2, NYISO 3, PJM 2) at THE PIN `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`, CAISO 3 + MISO 3 with sibling lanes (`FINDING-scn-ws5a-resolve-2026-09-06.md`); ERCOT's three are CCS-clean and stand at `1cc45bb2`, so the campaign sits at **two declared pins**. Post-fix, the 2030 REF CO2 level falls **54.3 % (NEISO) / 47.8 % (NYISO) / 1.58 % (PJM)** and the load-response **ΔCO2 falls 82 % / 42 %** — the correction does **not** cancel out of a delta, because it re-screens the retrofit fleet differently in the two arms. Gates 5/5 PASS on every re-solved leg (G1 unit identity `host rate × (1 − capture)`, zero failures). **The §1.1 volume-vs-shape headline survives the repair**; **no delta from a CCS-carrying ISO may be quoted from a pre-fix bundle**. CAISO and MISO re-solves are with sibling lanes. | — |
| 4 backcast byte-identity | yes (WS-1a: no key moves; keeper + forecast key list, FINDING §5) — **re-measured at the S2 floor** (SCN-WS1c): 0 keys moved, default `e5ecd4105ada3e58` stable, **0 of 90** committed `run_config.json` on the changed branch, backcast 2023–25 trajectories identical in all six ISOs; six keeper bundles named, `FINDING-scn-ws1c-2026-09-06.md` §4 | yes | yes (SCN-WS2a: six keeper keys byte-identical, FINDING §5) | yes (SCN-WS3b: **0 of 128** committed `run_config.json` keys moved on the changed branch — 18 backcast, 110 forecast — six keeper keys byte-identical, pinned default `e5ecd4105ada3e58` / backcast `6a2845e50951394e` unchanged; `mode="backcast"` + hindcast coercion to the dataclass defaults asserted by test; `FINDING-scn-ws3b-2026-09-06.md` §3) | yes | — |
| 5 matrix duty | stamped (`carbon_price_path` + `policy_bundle` rows minted at WS-1a) | stamped | stamped (`federal_ces_target` row + six cells, SCN-WS2a last commit) | stamped (`voluntary_clean_demand` base row + a `U` cell in all six shards, SCN-WS3b last commit) | stamped | — |
| 6 emissions grain | by fuel / by zone | by fuel / by zone | by fuel / by zone | by fuel / by zone | by fuel / by zone | **G-E1..E5 CLOSED** (SCN-WS0) |
| 7 registered probes on dashboard | **twelve arms** `{ercot,caiso,pjm,miso,nyiso,neiso}-2026-2027-scn-ws1-probe-{ref,carb}` (kind `scenario`, campaign `scn-ws1-probe`, each CARB paired to its REF) — SCN-WS1b-r2 **+ ERCOT Stage A-POLICY: `ercot-2026-2030-scn-campaign-policy-2026-09-06-{carb-lo,carb-mid,carb-hi,carb-mid-plus-load-hi}`** (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, each paired to `reference_case: REF`; solved at THE PIN `bdfb3095` in four owner-launched sub-lanes) **NEISO: NONE — all three `CARB-*` plus `CARB-MID+LOAD-HI` killed at phase 0 on a proven LP-input identity, never solved and correctly never registered** (SCN-WS5A-POLICY-NEISO). | **six ladder legs** `{ercot,neiso}-2026-2030-scn-ws2-ladder-{bau,ces-20,ces-40}` (kind `scenario`, campaign `scn-ws2-ladder`) — G-S5 CLOSED, the pruned POC evidence restored at HEAD **+ ERCOT: `ercot-2026-2030-scn-campaign-policy-2026-09-06-{ces-p10,ces-p20,ces-p30,ces-p20-plus-vol-hi}`** (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, at THE PIN) **+ NEISO: `neiso-2026-2030-scn-campaign-policy-2026-09-06-{ces-p10,ces-p20,ces-p30}`** (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, `reference_case: REF`) — the full ladder at the policy pin, all three 14/14 invariants PASS. | NEISO T0 pair `neiso-2026-2026-scn-ws2a-neiso-2026-t0-{ref,target}` (kind `scenario`) **+ ERCOT: `ercot-2026-2030-scn-campaign-policy-2026-09-06-{ces-t80,all-clean}`** (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, at THE PIN) **+ NEISO: `neiso-2026-2030-scn-campaign-policy-2026-09-06-{ces-t80,all-clean}`** (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`). | — **ERCOT: `ercot-2026-2030-scn-campaign-policy-2026-09-06-{vol-hi,ces-p20-plus-vol-hi,all-clean}`** (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, at THE PIN; VOL-MID killed at phase 0, never solved) **+ NEISO: `neiso-2026-2030-scn-campaign-policy-2026-09-06-{vol-mid,vol-hi,ces-p20-vol-hi,all-clean}`** (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`) — 4 of the lane's 9 legs carry the voluntary row; `vol-mid` is LIVE on NEISO, unlike ERCOT. | **19 arms**, campaign `scn-ws4-probe` (kind `scenario`): `{ercot,caiso,pjm,miso,nyiso,neiso}-2026-2026-scn-ws4-probe-t0-{ref,load-hi[,load-hi-organic]}` + `{ercot,neiso}-2026-2030-scn-ws4-probe-t1f-{ref,load-hi}`. The three ORGANIC arms are ERCOT/MISO/NYISO only — CAISO/PJM/NEISO killed at rule-29 phase 0 as byte-for-byte degenerate **plus 16 campaign arms**, campaign `scn-campaign-load-2026-09-06` (kind `scenario`, each case paired to `reference_case: REF`): `{ercot,caiso,miso,nyiso}-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi,load-hi-organic}` + `{pjm,neiso}-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi}` (PJM and NEISO ship a degenerate DC axis). **13 of the 16 were RE-REGISTERED UNDER THE SAME IDS post-capx-D77** by SCN-WS5A-RESOLVE, with each pre-fix bundle's slim artifacts deleted in the same commit (rule 26 `[R-DELETE]`); ERCOT's three keep their `1cc45bb2` bundles. A sidecar's `git.sha` and key provenance therefore say which pin its numbers are from — read it before quoting one. | `scn-ws0-smoke` REF/CARB pair |

**Emissions column, closed by SCN-WS0** (2026-09-05,
`docs/handoffs/FINDING-scn-ws0-2026-09-05.md`). G-E1: `emissions_by_fuel_mt` /
`emissions_by_zone_mt` in `_summarize_year`, each partitioning `emissions_mt`. G-E2:
`scripts/collate_scenario_campaign.py` sums across the ISOs present and labels the sum
"six-ISO modeled system", never "national". G-E3: `import_co2_mt_reported` +
`import_co2_basis`, reported beside the total and never inside it. G-E4:
`build_matrix_frame` carries every per-year scalar, and
`scripts/report_scenario_deltas.py` emits the case-vs-`--reference-case` delta set.
G-E5: twelve REF base YAMLs + `configs/scenario_campaign_matrix.yaml`. G-E6 (no marginal
rate) and G-E7 (NOx/SO2 unexported) stay OPEN and out of scope — both are disclosure
items the plan already records as such. Criterion 1's harness half is closed with them:
a case is now one field override, expressible in the campaign YAML or on the command
line via `--set`.

**The CES-target column's level became COMMITTED without a re-solve** (SCN-LEVELS 2026-09-06,
`docs/handoffs/FINDING-scn-levels-2026-09-06.md`). Owner card D-2 → S3 committed the §3.5
table; SCN-WS2a had built and probed the target row against exactly those values under an
"illustrative" label, so **no cell of this scorecard moved on the evidence** — rows 2, 4, 5
and 7 are untouched, row 1 changes only its label, and row 3's probe becomes quotable as a
campaign result rather than as machinery. No cache key moved (91 pre-existing keys measured
byte-identical) and no `ScenarioConfig` default changed. Two "illustrative" labels remain in
this plan OUTSIDE SCN-LEVELS' regions — §3 WS-2 item 5 and the §7 "WS-2a" prompt body — both
historical charter text for a landed lane; routed to SCN-DESK rather than edited.

**Load-HI row 1, closed by SCN-WS4b** (2026-09-06, `docs/handoffs/FINDING-scn-ws4b-2026-09-06.md`).
The named case is the two live keys SCN-WS0 shipped, now with their disclosure: `electrification_path`
as-is is `off` in all six ISOs (REF is the ScenarioConfig default; no `iso_configs` override); the
ERCOT `high` DC anchor drives the tail regime in 2030 only, and the ORGANIC companion attributes a
*shape* share in ERCOT/MISO/NYISO and nothing in PJM/CAISO/NEISO through 2030 (three solves WS-4c
need not spend). Rows 3 and 7 stay with SCN-WS4c.

**The Emissions column's first measured result is a leakage number, not a level.** The
exercising T0 (NEISO 2026, REF vs `carbon_price_delta=25`) cuts modeled in-ISO CO2 by
−2.71 Mt and simultaneously raises the reported import-attributed line by +1.85 Mt, all
of it on one NYISO seam rung — so roughly two thirds of the headline reduction leaves
the scored basis. Every campaign delta must be read with the import line beside it, and
§4's caveat block should carry that number per ISO (FINDING §5 item 2).

---

## 6. Owner decision boxes

| # | Decision | Recommendation | Why it needs the owner |
|---|---|---|---|
| **D-1** | Federal carbon price on a program ISO: **replace** the state trajectory (today), **floor** (`max`), or **additive**? | **Floor.** Additive double-charges a unit that already surrenders a state allowance; replace is a cut on NEISO/CAISO/NYISO in every year (G-C1). | Changes the resolved value of an existing registered field (`carbon_price_path`) on three ISOs; Q26 was a ruling on `carbon_price` and the owner should extend or distinguish it. |
| **D-2** | Campaign levels: carbon paths (RFF low/mid/high, or owner-supplied $/t knots), CES premium ladder ({10,20,30} stands from D8), **CES target schedule and ACP** (e.g. 80 % by 2035 / 100 % by 2050, `clean_capture`), voluntary levels, load-high pairing. | Take the §3.5 table as the default; the CES target and ACP are the two numbers with no precedent in the repo. | Scenario levels are the owner's what-ifs by definition; never a modeller's tuning. |
| **D-3** | Is a **voluntary clean-demand scenario axis** admissible, given ffr-5b's inadmissibility ruling on corporate PPA demand as a driver? | **Yes, as a declared, forecast-only, publicly-anchored axis** (§2.3) — the ruling was about a fitted driver. **D-3b:** in-LP hourly (24/7) matching stays deferred to the isolated portfolio tool. | ffr-5b is on record; only the owner can distinguish the classes. |
| **D-4** | Fund the `load-forecast` curated intake (published ISO low/mid/high energy+peak cases with DC decomposition)? | Optional; the campaign runs on the cited constants without it. Recommend **defer** until a scenario result is sensitive to the constant-vs-published gap. | Q23 ("I'm not getting more data") signals the posture; this is a different source class but the owner should say so. |
| **D-5** | Per-campaign §2.1b grant for the **NEISO scenario campaign** (Stage B) once WS-0…WS-4 land, and the order in which other ISOs' campaigns are asked for as their gates open. | Ask when Stage A's T1-F results are on the dashboard, not before. | Leg (d) is never standing. |
| **D-6** | Attribute netting rule between a federal CES row and a voluntary-demand row (voluntary counts toward the standard, or is additional to it). | Report both; default **counts toward** (one MWh, one claim — matches how RECs retire today). | Policy-design question, not a modelling one. |

**Card status (maintained by SCN-DESK; the live copy is
`docs/handoffs/scenario-desk-ledger-2026-09.md` §2).** **D-1, D-2, D-3, D-6 — PRESENTED
2026-09-05 (SCN-DESK r#1), awaiting ruling.** D-4 is held until WS-4a delivers its
constant-vs-published gap list; D-5 is held until Stage A's measured cost table is on the
forecast dashboard. Rulings are appended to the row above as `RULED <date>: …` and numbered
S1, S2, … in the ledger, in the refresh commit that receives them.

**UPDATED at SCN-DESK r#2 (2026-09-05, HEAD `db8b6015`) — no card ruled yet; all still open.**
- **D-1 RE-PRESENTED on new evidence.** SCN-WS1a's Phase-0 table (`FINDING-scn-ws1a-2026-09-05.md`
  §0.1/§6, machine-readable in `docs/handoffs/scn-ws1a/`) proves G-C1 numerically —
  `policy_bundle="tight"` is a carbon-price **cut of $16–$102/t in every one of 25 years** on
  CAISO/NYISO/NEISO — and adds the fact the plan did not have: **under the recommended floor the
  RFF mid path never once exceeds a program trajectory**, so a floor makes `tight` an exact
  **no-op** on those three ISOs rather than a fix. That raises two sub-boxes, now presented:
  **D-1(b)** what `tight` should mean on a program ISO once the floor is in, and **D-1(c)** how a
  federal floor composes with PJM's **partial** RGGI footprint.
- **D-3 RE-PRESENTED**, with `docs/handoffs/voluntary-clean-demand-design-memo-2026-09-05.md` §1
  as its brief; the memo raises **D-3b** (in-LP 24/7 matching stays deferred — recommended yes)
  and **D-3c** (the eligible set: renewable-only default, carbon-free as a labelled override,
  credit all eligible units or new builds only), both presented at r#2.
- **D-2** gains a named part from the same memo (box 5): the voluntary sub-levels `s_base`,
  `f_commit` and the WTP ceiling.
- **D-4 PRESENTED** — `FINDING-scn-ws4a-2026-09-05.md` §4 is the gap list, written to be presented
  unedited. Recommendation stands at **defer**, with the lane's own refinement: the intake's real
  prize is **G-D4-4, the wired-but-empty electrification layers**, not the growth rates.
- **D-5** still held: Stage A has not run.

**RULED 2026-09-06 (SCN-DESK r#5 amendment 1) — four cards, recorded verbatim as S1–S4.**
- **S1 — D-3: YES.** A voluntary clean-demand scenario axis is admissible as a declared,
  forecast-only, publicly-anchored, default-off axis; ffr-5b §1.4 is held to be about a *fitted
  driver*, a different admissibility class, and its null is preserved in REF and every scored
  lane. **D-3b rides it: in-LP hourly (24/7) matching stays DEFERRED** to the isolated
  `scope2-lce-portfolio` tool. Releases SCN-WS3b, then WS-3c.
- **S2 — D-1: FLOOR.** `effective = max(RFF path(year), program trajectory(year))` on a program
  ISO; the path alone elsewhere; `carbon_price` (scalar) keeps its Q26 replace semantics. Ruled
  with the measured consequence accepted: the RFF mid path never exceeds a program trajectory in
  any year, so the floor makes `policy_bundle="tight"` an exact **no-op** on CAISO/NYISO/NEISO
  rather than an increase (sub-boxes D-1(b)/(c) remain open). Releases the withheld WS-1a item 1
  as lane SCN-WS1c.
- **S3 — D-2: the §3.5 table is the COMMITTED default.** Carbon RFF low/mid/high; CES premium
  {10, 20, 30}; **CES target {2026: current, 2035: 0.80, 2050: 1.00}, ACP $50**; LOAD-HI = growth
  high + DC high. **No re-solve is owed** — SCN-WS2a built and probed against exactly these and
  labelled them illustrative, so the ruling changes the label, not the number.
- **S4 — D-4: FUND THE FULL DATATYPE.** All six published sources (ERCOT LTLF, PJM LTLF Table
  B-9b, NYISO Gold Book, ISO-NE CELT, CEC IEPR, MISO LTLF) curated through the data-intake skill.
  **This overrides both the plan's recommendation and SCN-WS4a's to defer** — recorded as such.
  Releases lane SCN-LOAD; the MISO driver-level 403 host wall is a known blocker flagged at the
  gate.
- **Still open:** D-3c (the voluntary eligible set — the WS-3a memo's box 3), D-6 (attribute
  netting; default "counts toward", report both), and D-5.

**D-7 — NEW, PRESENTED 2026-09-06 (SCN-DESK r#6).** *Does Stage A run before the CCS
emission-rate seam is repaired?* SCN-WS2b measured that retrofitted `gas_cc_ccs` units are
credited at 0.95 by the CES while carrying an **uncaptured** `emission_rate` in the dispatch
fleet (`emission_rate` 0.3745 → 0.3745 across a unit's own retrofit year, while `fuel_type` and
`heat_rate` both update correctly; three writes in one block of `ccs.py`, one overwritten
downstream). NEISO's 2030 CO2 answer is **sign-flipped**: +9.99 Mt as scored, −6.01 Mt with the
intended 90 % capture applied at fixed dispatch. **Scope:** every campaign case that moves
`gas_cc_ccs` — the CES cases, the carbon cases at or above `ccs_retrofit_available_year` (2028),
and `ALL-CLEAN` — i.e. most of Stage A's policy half. The repair is the capx D50/D60/D65 lane's
file, not this desk's, and is routed. Recommendation: **hold Stage A's policy half until the seam
is repaired**; the load half (`LOAD-HI`, `LOAD-HI-ORGANIC`) and the pure-carbon T0 probes below
2028 are unaffected and can proceed. The alternative — run Stage A now and re-run the affected
cases after the repair — spends the campaign's compute twice.
**RULED 2026-09-06 (SCN-DESK r#6 amendment 1) — S5: HOLD THE POLICY HALF, RUN THE LOAD HALF NOW.**
Stage A splits at the `gas_cc_ccs` line: **A-LOAD** (`REF` / `LOAD-HI` / `LOAD-HI-ORGANIC` six-ISO
T1-F + the sub-2028 carbon T0 probes) released, issued when SCN-WS4c landed (r#7), running as
`SCN-WS5A-LOAD`; **A-POLICY** (every CES case, every carbon case at or above 2028, `ALL-CLEAN`,
`VOL-*`) HELD until the capx CCS emission-rate seam is repaired and a paired check confirms
`emission_rate` follows the retrofit. *(This `RULED` line was owed at r#6 am.1 and appended at r#9 —
the ruling itself was recorded in the desk ledger §2 at the time.)*

**D-8 and D-9 — NEW, PRESENTED 2026-09-06 (SCN-DESK r#9); desk cards, live copy in the ledger §2.**
**D-8:** SCN-WS3b — relaunch under a third stem now, hold until the CCS repair lands, or drop the
voluntary axis from Stage A? Two stems produced nothing across three refreshes; recommendation
**relaunch now** (zero-LP build, ready-in-waiting). **D-9:** direct the capx director to charter the
CCS emission-rate seam repair as a named lane? At capx r#45 the seam is named but no lane carries it,
and it is the sole release condition for Stage A-POLICY; recommendation **yes**.
**RULED 2026-09-06 (SCN-DESK r#9 amendment 1) — S6 (D-8): "Relaunch now, third stem"** → SCN-WS3b-r3 issued (`claude/scn-ws3b3-voluntary-demand-q7mv`; the VOL-* cases stay S5-held). **S7 (D-9): "Yes, name it the capx director's next lane"** — routed to the capx ledger as an owner direction; the S5 paired check (`emission_rate` follows the retrofit) is that lane's gate; the desk charters nothing on the seam.
**S7 EXECUTED (capx D77, `ae8dd2a0`, PR #5089, 2026-09-06):** the repair is on main (a `ccs_capture_fraction` stamp composed at both measured-rate restoration sites; no cache key moves, so pre-fix bundles reaching 2028 with a retrofit are silently stale at their own key); the NEISO screen and FINDING are owed.

**D-10 — NEW, PRESENTED 2026-09-06 (SCN-DESK r#10); desk card, live copy in the ledger §2.** SCN-WS5A-LOAD measured that S5's premise was false: the retrofit screen is armed by the STATE carbon program, so NEISO's reference case carries 8.8 GW of `gas_cc_ccs` (NYISO 6.5 GW), mis-rated pre-D77 — NEISO 2030 CO2 overstated by 5.60 Mt (41.9 %), NYISO by 5.29 Mt (25.3 %). Question: re-pin the campaign once post-D77 and re-solve only the five contaminated legs plus CAISO (recommended), finish at the frozen pin and re-solve afterwards, or finish and disclose. A-POLICY's S5 release condition is unchanged and needs no card: it releases when the model-grain paired check lands (D77's screen or the re-solved NEISO REF).
**RULED 2026-09-06 (SCN-DESK r#10 amendment 1) — S8: "Re-pin once post-D77 now."** The SCN-WS5A-LOAD amendment is issued: PJM/MISO finish at the frozen pin, NEISO + NYISO re-solve and CAISO solves at a post-D77 pin under a hunk-by-hunk G-DRIFT, ERCOT/PJM/MISO stand on empty retrofit ledgers; the re-solved NEISO REF is S5's model-grain paired check, so Stage A-POLICY releases the refresh it lands with no further card.

**STAGE A-POLICY RELEASED 2026-09-06 (SCN-DESK r#11) under ruling S5, no new card:** capx D77's FINDING (`3d748d02`) carries the paired check S5 named — the identity `emission_rate = measured × (1 − 0.90)` PASS to 1e-9 on every converted NEISO unit in every year of a real t1f solve. The six `SCN-WS5A-POLICY-<ISO>` charters are issued (CARB-LO/MID/HI, CES-P10/P20/P30, CES-T80, CARB-MID+LOAD-HI), solves gated on the load campaign's post-D77 pin and the carbon-form switch (SCN-FIX1). **D-2(b), D-3c and D-6 PRESENTED** so VOL-MID / VOL-HI / CES-P20+VOL-HI / ALL-CLEAN can be added by addendum; CAP-STATE-TIGHT stays out on its unruled level.
**RULED 2026-09-06 (SCN-DESK r#11 amendment 1) — S9 (D-2(b)): "Take the placeholders as committed"** (`f_commit` mid 0.5; WTP ceiling $4.5/MWh); **S10 (D-3c): "Ratify the default as built"** (renewable-only eligible set; nuclear/CCS only via the labelled override); **S11 (D-6): "Counts toward; report both."** The four voluntary legs join the six policy lanes by addendum; CAP-STATE-TIGHT is the only §3.5 case still out of Stage A.
**D-2(c) — PRESENTED 2026-09-06 (SCN-DESK r#12):** `CAP-STATE-TIGHT`'s budget slope (WS-1a §4.2: linear decline to 20 % of the 2025 published per-state budget by 2050; CAISO REF-anchored) and the schedule field `mass_cap_tons_by_year` it needs, absent at HEAD. Recommendation: commit the slope and charter the field.
**RULED 2026-09-06 (SCN-DESK r#12 amendment 1) — S12: "Commit the 80 % slope and build the field."** SCN-CAP issued (the field, the case, the matrix row); CAP-STATE-TIGHT joins the three program-ISO policy lanes as a thirteenth case gated on the field landing. **Every §3.5 case is now inside Stage A.**

**D-5 PRESENTED 2026-09-06 (SCN-DESK r#13).** Stage A-LOAD's measured cost table exists (synthesis §8: 313.7 min of LP for 16 legs / 80 solve-years, 3.92 min per solve-year, ~4.7 h wall; NEISO 1.09 min per solve-year). Recommendation: **HOLD** the NEISO Stage-B grant until SCN-WS5A-RESOLVE lands the post-D77 re-solve (the pre-D77 NEISO REF carries a 41.9 %-contaminated 2030 CO2 level) and the policy half has run; note SCN-FIX2's finding that `CARB-HI` is live on NYISO/NEISO only at full horizon (2031–2047).
**RULED 2026-09-06 (SCN-DESK r#13 amendment 1) — S13: "Hold until RESOLVE and the policy half land."** No grant; re-presented when both are on main.

**D-11 — NEW, PRESENTED 2026-09-06 (SCN-DESK r#17); desk card, live copy in the ledger §2.** The solve slot. `SCN-WS5A-POLICY-ERCOT` is fully prepared — phase 0 done, eleven of thirteen legs surviving (`VOL-MID` and `CAP-STATE-TIGHT` killed on proven identities), PRECOMMIT on main — and is blocked only by the policy charter's own precondition P4, which allows ONE repo-wide solve while `SCN-WS5A-RESOLVE` is on PJM/CAISO/MISO. **CLAUDE.md rule 12's own cap is ~2 concurrent per-plant multi-zone runs**, so P4 was stricter than the rule; it was written that way because this desk cannot observe how many solves the capx track has live. RESOLVE still owes 7 heavy legs. Measured peaks: MISO 9.65 GB, CAISO 4.87 GB, ERCOT 4.2 GB on a 15 GB box. Recommendation: **relax P4 to rule 12's ~2 cap** — ERCOT never shares a fleet with PJM/CAISO/MISO, so the two solves are independent, and the alternative parks eleven prepared legs behind seven heavy ones.
**RULED 2026-09-06 (SCN-DESK r#17) — S14: "Relax P4 to rule 12's ~2 cap (Recommended)."** ERCOT's first solve is released and may run concurrently with RESOLVE's remaining legs, under two conditions carried into policy charter **v6**: at most **2 SCN-track solves at once, on different ISOs**, and **not while the capx track is mid-solve** — the owner sequences that half, being the only party who sees both tracks. The stricter one-solve reading of P4 is retired; rule 12's text governs. No other precondition moves.

**D-12 — NEW, PRESENTED 2026-09-07 (SCN-DESK r#18); desk card, live copy in the ledger §2.** The CES premium ladder cannot discriminate on entry in five of six ISOs at the committed levels. The entry screen folds `attr = max(EAC, rps_credit_for_zone, clean_credit)` with **no fuel gate on the RPS leg** (`new_entry.py` ~:1132–1143), so where a state RPS sits at its escape a federal CES premium below it adds nothing to entry revenue. `STATE_RPS_ACP` = MISO 30 · NYISO 40 · PJM 45 · CAISO 50 · NEISO 50 · **ERCOT absent**; the committed ladder {10, 20, 30} and the voluntary ceilings {$4.50, $7.00} sit under every one, and `CES-T80`'s ACP $50 ties exactly on CAISO and NEISO. Found independently by two lanes (NEISO's byte-identical VOL-HI/VOL-MID pair at `rps_dual` 50.0 in 5/5 years; PJM's phase 0). Not a defect — rule 19's `max()` doctrine, and economically correct. The retirement leg **is** fuel-gated, so the CES legs still differ and still solve. Recommendation: add one bracketing leg above the mask.
**RULED 2026-09-07 (SCN-DESK r#18) — S15: "Add one bracketing leg above the mask."** Each lane measures its own REF RPS dual per year at zero LP; where the mask binds it adds a single **`CES-P60`** leg — ONE common level for every ISO, above the footprint's highest published ACP ($50), identified from published ACPs and never from a residual, deliberately not per-ISO so it cannot become the per-ISO fitting rule 25 forbids. ~5 legs / ~100 min LP. It converts a null into a measured threshold and falsifies the alternative reading that the CES row is not wired; a leg that clears the mask and still moves nothing is a reportable finding, not a gate failure. Ruling S3's committed §3.5 levels are untouched — a bracketing leg beside the ladder, not a re-levelling of it.

**RULED 2026-09-07 (SCN-DESK r#18 amendment 1) — S16, owner instruction, not a desk card:** *"I don't want to run all of these in one session per iso though that's way too much compute and we have effectively unlimited ability to run lps in parallel so the per iso session should launch shards itself"* + *"Update those prompts accordingly to launch individual sessions for runs to target <1 hr of lp solve per session."* The per-ISO policy lane becomes a **coordinator** — it keeps phase 0, the PRECOMMIT, keys, kills, gate scoring, the FINDING, the plan §5.1 rows and the matrix cells, and **launches one shard session per leg-group**, each sized under 60 min of LP. Shard size is derived from the Stage A-LOAD synthesis §8 measured min/solve-year at 5 solve-years per leg: NEISO 10 legs/shard · ERCOT 9 · NYISO 2 · CAISO 2 · MISO 2 · **PJM 1** (PJM's within-window profile is super-linear). Rule 12's ~2-concurrent cap is a per-container memory constraint and does not compose across shards; its within-invocation half — one solve at a time, years always sequential — is untouched. Codifies what ERCOT's SUBLANE protocol, PJM's S2/S3/S4/S6 split and NYISO's four containers had already converged on. Charter **v7** + the shard template: ledger §5.5.

**D-13 — NEW, PRESENTED AND RULED 2026-09-07 (SCN-DESK r#19); desk card, live copy in the ledger §2.** `CAP-STATE-TIGHT` is a policy LOOSENING, not a tightening. NEISO refused the kill the charter and `FINDING-scn-cap` §3 both ordered, solved the case, and measured it BINDING in all five years at **+2.9 to +13.9 Mt** — emissions equal to the budget to 3.2e-13 relative — with a dual of **12.23 → 8.26 $/t** against the RGGI adder it REPLACES at **26.05 → 34.15**, permitting up to 293 % more emissions and building LESS clean capacity than REF (2030: 287.4 vs 1,198.0 MW). A mass cap on a 2050 glide is generous in a 2026–30 window while a price path rises. Desk recommendation: keep the S12 level and rename/reframe.
**RULED 2026-09-07 (SCN-DESK r#19) — S17: "Drop the case from Stage A, route to Stage B."** *(Owner took the third option, against the desk's recommendation.)* The case leaves the §3.5 Stage-A set: CAISO must not solve it, PJM drops it, MISO was never in scope. NEISO's and NYISO's already-registered cap legs stay registered (un-registering would strand a bundle and redden the parity gate) but are **excluded from the Stage-A synthesis and from §5.1**, and carried forward as the **Stage-B seed evidence**. **Ruling S12 is NOT withdrawn** — the 80 %-decline slope, `mass_cap_tons_by_year` and the case definition stand as built; only the stage moves. Stage A keeps a clean **price-only** policy axis, and the price-vs-quantity comparison is re-asked at full horizon where the glide can bite.

---

## 7. Session prompts (paste whole; house style per FF plan §6)

Every prompt implicitly begins: *Read `CLAUDE.md`, `docs/forecast-development-plan-2026-07.md`
(§2.1b, §2.4, §7 bind), `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` (this
plan — your workstream section is your charter), and the mechanism matrix
(`docs/mechanism-testing-matrix.md` + `docs/codebase-site/data/mechanism-matrix/<ISO>.js`
for every ISO you touch). Fresh branch off latest `origin/main`. Zero solves until your
PRECOMMIT is pushed. Push by pack size (CLAUDE.md "Git & Pushing"); verify every pushed
file ≥ 300 lines. Findings doc to `docs/handoffs/FINDING-scn-<ws>-<date>.md`; update this
plan's §5.1 scorecard row in the same PR.* Model labels: `[FABLE]` / `[OPUS]`.

### WS-0 `[OPUS]` — emissions grain + scenario harness

```
You are lane SCN-WS0 (Forecast Scenario Readiness plan §3 WS-0). DATA PROFILE: neiso
Zero-solve build, then ONE paired T0 (NEISO 2026, REF vs carbon_price_delta=25) to exercise it.
Deliver, in this order, each its own small commit:
1. results/export.py::_summarize_year gains emissions_by_fuel_mt (same fuel keys as
   generation_twh), emissions_by_zone_mt, import_co2_mt_reported (Σ import-tranche MWh × its
   IMPORT_TRANCHE_EF; NEVER added into emissions_mt — bake the disclosure string into the
   summary), unserved_mwh. Populate DispatchResult.emissions at solve time from dispatch ×
   FleetContext.emission_rate so run_full_horizon._co2_tons reads it byte-identically.
   Trivial-first tests (1 gen / 1 zone / 24 h): by-fuel and by-zone sum to emissions_mt exactly.
2. matrix.py::build_matrix_frame carries every _summarize_year scalar + unserved_mwh (envelope
   unchanged). New scripts/report_scenario_deltas.py generalized from report_ces_campaign.py:
   --reference-case, per-ISO capacity / generation / CO2-by-fuel deltas per year, cumulative CO2
   delta, evolution-ledger deltas, captured prices, curtailment. report_ces_campaign.py keeps
   its premium tables and delegates the generic ones (tests/scoring/test_report_ces_campaign.py
   must stay green).
3. scripts/collate_scenario_campaign.py: sums emissions_mt across the ISOs present, reports the
   three side lines (import-attributed, unserved, ISOs not modeled), labels the sum "six-ISO
   modeled system", never "national"; campaign-level delta table.
4. configs/scenarios/<iso>_scenario_base_2026_2050.yaml and _2026_2030.yaml for all six ISOs
   (ISO + horizon only); configs/scenario_campaign_matrix.yaml in cases: mode with the plan §3.5
   case set — cases whose fields do not exist yet (federal_ces_target_by_year,
   voluntary_clean_demand_path) are listed COMMENTED with a "lands in WS-2/WS-3" note, never as
   live keys. A generic --set field=value override on run_full_horizon.py and run_ces_leg.py,
   validated against ScenarioConfig field names, recorded in run_config.json.
5. register_forecast_run.py: a `scenario` kind with campaign / case / reference_case meta; the
   run explorer groups by campaign and shows the CO2 delta-vs-reference sparkline.
6. The paired T0 through the new tables; register both arms (kind scenario, campaign
   scn-ws0-smoke). No matrix cell moves (no mechanism tested). FINDING + scorecard row.
Rules that bite here: 2 (no hour loops in any new accounting — numpy over the parquet), 5, 24,
27, FF plan §7.5 (forecast namespace only). No CI workflow. No default moves.
```

### WS-1a `[FABLE]` — federal carbon-price semantics + the two seam defects

**STATUS: fully executed.** Items 2–4 + Phase 0 + the D-1 evidence memo landed at SCN-WS1a
(`FINDING-scn-ws1a-2026-09-05.md`), which correctly WITHHELD item 1 on the open card. Owner
ruling **S2** (2026-09-06, desk ledger §2) then signed D-1 = **FLOOR**, and **item 1 was
executed by lane SCN-WS1c** (`PRECOMMIT-scn-ws1c-2026-09-06.md`,
`FINDING-scn-ws1c-2026-09-06.md`): the floor, the D34 guard's path-branch sibling, the
`test_cap_and_trade.py:135` flip, the cache-epoch entry, and the byte-identity key list —
0 keys moved, 0 of 90 committed run_configs on the changed branch. **Item 1's "NEISO-tight
strict-increase test" was written as `tight ≥ current` with equality on the program ISOs**: the
floor makes `tight` an exact no-op on CAISO/NYISO/NEISO, so a strict assertion is false — the
ruling moved the predicate (FINDING §3). **D-1(b) and D-1(c) remain OPEN.**

```
You are lane SCN-WS1a (plan §3 WS-1 items 1–3). DATA PROFILE: caiso (for the G-C2 reproduction)
Owner box D-1 must be signed FLOOR before you change cap_and_trade.py; if it is not, deliver
items 2–3 and the D-1 evidence memo only.
Phase 0 (zero-solve, push before any code): a table of the resolved carbon trajectory per ISO
per horizon year for policy_bundle current / tight / rollback at HEAD, proving G-C1 (tight is a
CUT on CAISO/NYISO/NEISO in every year). This is the PRECOMMIT.
1. Floor semantics: cap_and_trade.py:289-291 — an explicit non-"zero" carbon_price_path yields
   effective = max(RFF path(year), program trajectory(year)) on a program ISO, the path alone
   elsewhere. carbon_price (scalar) keeps Q26 replace + guard, untouched. Extend the D34 guard
   to the path branch. Update tests/unit/policy/test_cap_and_trade.py:135 to the floor; add the
   NEISO-tight strict-increase test over 2026–2050. Cache-epoch entry in results/cache.py.
   Byte-identity proof: every keeper cache key + every committed forecast bundle's key (all
   carry path "zero") unchanged — list them.
2. G-C2: reproduce with a CAISO T0 (2026, one solve-year; the WECC unspecified block's offer
   must move by 0.428 × price under carbon_price_delta=25 through spec.py's seam), then
   spec.py:1931 → resolve_carbon_price(config, year). Same T0 after: moved.
3. G-C3: build the membership-weighted per-generator column in runner.py's assemble_mc call
   exactly as scripts/run_calibration.py:4022-4052, same gate; assert scalar-path byte-identity
   for every uniform-membership ISO in a unit test.
4. Pre-declare (do not run) the CAP-STATE-TIGHT case config (mass_cap_tons schedule on the
   program ISOs) and confirm the cap row's slack/dual are in the exported summary.
Matrix: re-stamp carbon_price_path cells in all six shards with the new semantics + citation;
policy_bundle likewise. FINDING + scorecard. Rules 1, 19, 24, 26, 27, 28.
```

### WS-1b `[OPUS]` — six-ISO carbon paired probe + NEISO/ERCOT T1-F ladder

```
You are lane SCN-WS1b (plan §3 WS-1 items 4–6). DATA PROFILE: all
Precondition: WS-0 and WS-1a merged. PRECOMMIT first: the expected sign and order of magnitude
per ISO (Δprice ≈ Δcarbon × marginal fossil rate in fossil-marginal hours; coal→gas re-order
where coal exists; CCS retrofit screen response where ≥ 2028).
1. Six paired T0 runs (2026 only): <iso>_scenario_base_2026_2030.yaml with --end-year 2026,
   REF vs --set carbon_price_path=mid. Score P1-style + the structural gate (rule 29 STOP gate:
   direction, magnitude, footprint confined to fossil rows). Register all twelve arms
   (kind scenario, campaign scn-ws1-probe).
2. NEISO then ERCOT T1-F 2026–2030: REF + CARB-LO/MID/HI via market-sim matrix (--workers 2,
   never both ISOs at once with MISO/PJM). Reuse any committed REF at the same cache key.
   report_scenario_deltas + collate on the two ISOs. Invariants I1–I14 per leg; FC-6 P1 on the
   REF/MID pair.
3. Matrix: carbon_price_path cell per ISO → evidence citation; mass_cap_enabled stays U.
FINDING with wall/RSS per solve-year; scorecard rows. Never quote a HOLD ISO's 2030 mix as a
result — the deployment delta is a delta between two runs that share the ISO's live FC-1 defects.
```

### WS-2a `[FABLE]` — the endogenous national CES target row

```
You are lane SCN-WS2a (plan §3 WS-2 items 1–2). DATA PROFILE: neiso
Owner box D-2 supplies the target schedule/ACP; use the illustrative {2026: current, 2035: 0.80,
2050: 1.00} / ACP $50 if unsigned and say so.
1. One annual federal CES row per ISO on the clean-tier row machinery (rows.py:145-202), as a
   federal region spanning every load zone; coefficients = federal_ces.unit_credit_fractions
   (both crediting modes unchanged); escape column at the ACP; dual → clean_attribute_price_by_fuel
   → the existing max() seam (no new consumer). Relax rows.py:1346's "requires the RPS region
   family" so the federal row stands alone or beside state rows; K-row/clean-tier byte-identity
   for MISO proven by test. Vectorized; one row per year.
2. Fields: federal_ces_target_by_year (sparse knots, None = no row), federal_ces_acp_usd_per_mwh;
   __post_init__ guard: target row and a non-zero exogenous premium are mutually exclusive
   (rule 19); forecast-only coercion; _CACHE_KEY_OPTIONAL_FIELDS at None. Matrix row + six
   shard cells in the same PR (CI enforces).
3. Postures documented + tested: state rows + federal row (default), federal_ces_replaces_state_rps,
   state only. Trivial-first tests: 1 gen / 24 h binding row dual = (mc_clean − mc_dirty);
   escape case dual = ACP.
4. Probe: NEISO 2026 T0, REF vs the target row. Structural gate: binds or escapes; dual = ACP iff
   escape fires; credited share ≥ target otherwise; CO2 falls; footprint = eligible columns.
Update docs/codebase/05-policy.md and the constraints.py docstring (G-S6). FINDING + scorecard.
```

### WS-2b `[OPUS]` — premium ladder re-prove at HEAD + national clearing script

```
You are lane SCN-WS2b (plan §3 WS-2 items 3–6). DATA PROFILE: ercot (then neiso)
1. Re-run the FF-3B POC at HEAD posture: ERCOT 2026–2030, configs/ces_premium_matrix_poc.yaml
   (BAU + CES-20 + CES-40) via scripts/run_ces_leg.py one leg per invocation; then NEISO the same
   ladder. Register (kind scenario, campaign scn-ws2-ladder). In the FINDING, compare the 2030
   surface to ff-3b-ces-poc-2026-07.md table by table: direction must hold; attribute every
   level change to a named default flip since July (retirement rule, fossil dated exits, CCS
   capex scaling, entry dampers, DC posture).
2. scripts/ces_national_clearing.py (zero-solve): from a campaign's premium legs, interpolate
   each ISO's clean-share-vs-premium curve and solve for the uniform premium meeting
   Σ_ISO credited MWh ≥ target × Σ_ISO load per year; report per-ISO shares at that premium
   beside the per-ISO target-row result (WS-2a) and the spread. Tests on synthetic curves.
3. Matrix: federal_ces_enabled cells for ERCOT and NEISO re-stamped with HEAD-posture evidence.
Wall/RSS per solve-year in the FINDING; scorecard rows.
```

### WS-3a `[FABLE]` — voluntary clean-demand design memo (no code)

```
You are lane SCN-WS3a (plan §3 WS-3 item 1). DATA PROFILE: code
Memo-first (FF-0C / FF-G4 pattern): docs/handoffs/voluntary-clean-demand-design-memo-<date>.md.
Sections: (0) bottom line; (1) the ffr-5b ruling and why a declared scenario axis is a different
admissibility class (rule 13 reproducibility + rule 20 DOF, argued line by line — owner box D-3);
(2) representation options — annual volumetric attribute row with a willingness-to-pay escape
(recommended), hourly-matched T-row block (deferred, with the LP-shape and portfolio-problem
reasons; the scope2-lce-portfolio tool is the 24/7 instrument), entry-screen-only price adder
(rejected: no dispatch footprint) — each against rules 1, 2, 19; (3) the DC-linked volume
construction and its public anchors (NREL voluntary market status report, CEBA public aggregate,
hyperscaler commitments, EIA-861 commercial load share for allocation) with a per-cell
sourced / needs-citation table; (4) eligibility (wind/solar/geothermal; nuclear/CCS as an owner
box) and the netting rule vs a federal CES (owner box D-6); (5) fields, coercion, cache-key and
matrix duty; (6) the probe design and its structural gate; (7) decision boxes for the owner.
No code, no solve, no default. Cite file:line for every claim about the existing seams.
```

### WS-3b `[FABLE]` build + WS-3c `[OPUS]` probe — issued only after D-3 is signed

```
(WS-3b) You are lane SCN-WS3b. DATA PROFILE: ercot. Build exactly the memo's signed design:
policy/voluntary_demand.py (volume resolver, eligibility, WTP), the row on the shared row
family (after WS-2a's coupling change), fields voluntary_clean_demand_path /
voluntary_wtp_ceiling_usd_per_mwh / voluntary_eligible_fuels with forecast-only coercion and
cache-optional at off, constants with citations, matrix row + six cells, trivial-first tests
(binding: dual = clean-minus-dirty gap; ceiling: dual = WTP, escape = shortfall). Backcast keys
byte-identical — list them. FINDING + scorecard.
(WS-3c) You are lane SCN-WS3c. DATA PROFILE: ercot. PRECOMMIT the expected footprint, then
ERCOT 2026 T0 REF vs voluntary mid: the row binds; dual positive and below WTP; curtailment
falls before dispatch changes; CO2 falls; only thermal rows displaced. Then ERCOT T1-F 2026–2030
REF + VOL-MID + VOL-HI for the entry-wave response. Register; stamp the ERCOT cell; FINDING.
```

### WS-4 `[OPUS]` coherence + `[FABLE]` adequacy reading

```
You are lane SCN-WS4 (plan §3 WS-4). DATA PROFILE: all
1. Named cases LOAD-HI (growth high + DC high) and LOAD-HI-ORGANIC (growth high + DC mid) in
   configs/scenario_campaign_matrix.yaml with the ERCOT tail-regime arithmetic
   (datacenter.py:318-320) disclosed in the case comment.
2. DATACENTER_ZONE_SHARE for ERCOT and MISO from published large-load queue geography (cite the
   ERCOT LFL officer update and the MISO LTLF DC decomposition), replacing the load_share
   fallback; shares sum to 1.0 (datacenter_zone_shares raises otherwise). Re-check NEISO's {}
   against the 2026 CELT and record the immateriality arithmetic.
3. [FABLE half, may be a separate session] Pre-declared adequacy reading per ISO under LOAD-HI:
   curve-ON ISOs report backstop-built gas_ct separately in the delta tables; ERCOT reports
   unserved energy beside CO2. No I7/I12/I3 fix is chartered here — disclose per case.
4. Six T0 probes (2026, REF vs LOAD-HI): CO2 rises ≈ fossil-average rate × added fossil-served
   MWh; unserved reported; price rises. NEISO + ERCOT T1-F 2026–2030 for the deployment response.
   Register (campaign scn-ws4-probe); stamp demand_growth_path / datacenter_load_path cells.
5. Owner box D-4 (load-forecast intake) is NOT executed here; list the constant-vs-published
   gaps you noticed for the box.
FINDING with wall/RSS; scorecard rows; spec §"demand" note routed to /sync-docs (G-L1).
```

### WS-5 `[OPUS]` — Stage A campaign (issued after WS-0…WS-4 land)

```
You are lane SCN-WS5-A. DATA PROFILE: all
Solve configs/scenario_campaign_matrix.yaml for every ISO at 2026–2030 (≤ 5 solve-years; no
§2.1b grant needed) with market-sim matrix / run_ces_leg.py, ≤ 2 concurrent invocations and one
when MISO or PJM runs (rule 12). Reuse every committed REF at the campaign's cache key. Per ISO:
report_scenario_deltas; then collate_scenario_campaign across the six. Register every leg (kind
scenario, campaign scn-campaign-<date>). Re-run the FC-6 paired battery on the campaign's own
REF/CARB-MID pair per ISO. Deliver the Stage-A section of the synthesis memo (plan §3 WS-5
Stage C outline): dispatch deltas, first-wave deployment deltas, per-ISO and six-ISO CO2 deltas
with the three side lines, interactions, honest-unfit list per ISO from its live FC map. Present
owner box D-5 (the NEISO Stage-B grant) with the measured Stage-A cost table. Never a full-horizon
leg without the grant.
```

---

## 8. Findings filed by this survey (for the repair lanes; none fixed here)

| id | severity | where | what |
|---|---|---|---|
| G-C1 | design defect, live in `policy_bundle="tight"` | `policy/cap_and_trade.py:289-291` | explicit RFF path suppresses the projected state-program price in forecast; on CAISO/NYISO/NEISO every RFF path is below the program trajectory, so "tight" and any path-written federal price is a carbon-price **cut** there — the D23 inversion via a second field; the D34 guard does not cover it |
| G-C2 | seam defect | `model/interchange/spec.py:1931` | border-carbon adder built from raw `config.carbon_price`, not the resolver; $0 under the default program-resolved posture |
| G-C3 | forecast/backcast asymmetry | `runner.py:2561-2575` vs `scripts/run_calibration.py:4022-4052` | membership-weighted carbon column built only on the backcast path; inert today (PJM forecast adder $0), live under any partial-footprint federal stacking |
| G-S3 | coupling | `model/lp/rows.py:1346` | clean-tier rows require the RPS region family (MISO-only) — blocks a federal all-zone clean row |
| G-S5 | records | `frontend/data/hindcast/` | CES-POC sidecars pruned 2026-09-05; POC evidence survives only in `ff-3b-ces-poc-2026-07.md` |
| G-E1/E2/E3/E4 | output surface | `results/export.py:198-210`, `matrix.py:113-178`, `import_nodes.py:100-104` | no CO2 by class/zone/hour; no six-ISO sum; imports zero by design; matrix frame is `emissions_mt` only with no delta table |
| G-L3 | scenario coherence | `constants.py:2858+`, `datacenter.py:318-320` | growth-high and DC-high are independent axes; ERCOT DC-high enters the additive tail regime — the high case needs a declared pairing |
| G-L5 | records | `uncertainty.py:264-270` | `datacenter_percentile` / `electrification_percentile` documented as sampler levers but never drawn |
| G-S6 | docs | `policy/constraints.py:5-6` | docstring names RPS; module implements only the mass cap |
| spec | docs | `model-methodology-spec.md:728,801,822` | demand growth documented as the bare scalar; DC block / electrification layers / vintage seam absent |

---

## 9. Ledger

- 2026-09-05 — v1. Planning session on branch `claude/market-sim-forecast-scenarios-md777o`;
  survey verified at `4d4dc6ce`. Zero solves, zero code, zero defaults. Owner boxes D-1…D-6 open.
- 2026-09-05 — **Scenario Readiness Desk opens (SCN-DESK r#1, main HEAD `d01ab8b0`).** Ledger
  created at `docs/handoffs/scenario-desk-ledger-2026-09.md`. **Wave 1 issued in full** —
  SCN-WS0 (`claude/scn-ws0-k7m2`), SCN-WS1a (`…-p4qd`), SCN-WS2a (`…-t9xb`), SCN-WS3a
  (`…-r6vn`), SCN-WS4a (`…-h3zc`); five disjoint-file lanes, none needing an owner ruling to
  start. The §7 "WS-4" prompt is **split** — items 2+5 to WS-4a now, items 1+3 to WS-4b and
  item 4 to WS-4c in wave 2 (both depend on WS-0's harness); WS-1a's item 1 is **gated** on
  D-1. No other §7 body edited. **Cards D-1, D-2, D-3 and D-6 PRESENTED**; D-4 held for
  WS-4a's gap list and D-5 for Stage A's cost table, per the plan's own §6 timing. Capx
  deconfliction against director r#40: no HOLD required — D60-R2 (running) holds
  `scripts/forecast_verdict.py` and `frontend/data/forecast/`, which no SCN lane touches; the
  six matrix shards are the one live shared surface and carry the last-commit one-line
  protocol. §2.1b gate at the pin: **NEISO only** (NYISO's `complete` withdrawn again
  2026-09-05, so Q45's premise has lapsed) — no Stage-B lane is issuable and none is issued.
  Zero solves, zero code, zero defaults, zero markers.
- 2026-09-05 — **SCN-DESK r#2 (main HEAD `db8b6015`).** All five wave-1 lanes launched and landed
  work in one day. **Complete:** WS-1a (items 2–4 + Phase 0 + the D-1 memo; item 1 correctly
  withheld on the open card), WS-3a (the memo, launched twice, no divergence), WS-4a (ERCOT
  already populated — this plan's §2.4 "only for PJM" line was **stale** and is corrected; MISO
  populated and validated on published totals; NEISO `{}` re-confirmed; the D-4 list delivered).
  **Checkpoints:** WS-0 (items 1–4 + PRECOMMIT; the `scenario` registration kind and the paired
  T0 owed) and WS-2a (the target row + two fields; postures, probe, matrix and docs owed).
  **Graded against claim:** no matrix row or cell exists for `carbon_price_path`, `policy_bundle`
  or `federal_ces_target_by_year` — WS-1a's own scorecard edit claimed the first two were
  stamped and the lane made zero commits to `docs/codebase-site/data/`; WS-2a added two
  solve-affecting fields with no row **and CI exited 0**, so `check_mechanism_matrix.py`'s duty-(c)
  half did not fire. Both routed, neither fixed here. **Issued:** SCN-WS0-R, SCN-WS2a-R, SCN-MX-R
  (a rule-28 repair charter and the sole matrix-tree writer until it merges), SCN-WS4b (unblocked;
  campaign-YAML ownership transferred to it). WS-1b / WS-2b / WS-4c blocked on WS-0's item 5;
  WS-3b blocked on card D-3 alone, both its code preconditions now met. §2.1b gate unchanged —
  NEISO only; no Stage-B lane issuable, none issued. Zero solves, zero code, zero defaults.
- 2026-09-06 — **SCN-DESK r#5 + amendment 1.** Wave 2 essentially in: SCN-WS2a landed complete
  (probe registered, FINDING, matrix row + one cell per shard as its last commit), SCN-WS4b landed
  both named cases and six pre-declared per-ISO adequacy readings, SCN-MX-R-r2 landed its CI
  diagnosis and the epoch entry; SCN-WS1b and SCN-WS2b in flight with PRECOMMITs pushed before
  their solves. **Two desk corrections against its own record:** the r#4 LOST call on SCN-WS4b is
  withdrawn (launched late, not never launched), and the desk's three-refresh claim that the
  matrix guard "did not fire" on PR #4870 is withdrawn — it fired, failed, and the PR merged five
  seconds after creation with seven red checks; the desk had been reading the checker's
  validate-only mode as a registration verdict. **Amendment 1 records owner rulings S1–S4** (§6)
  and issues the four lanes they release: SCN-WS1c (floor), SCN-WS3b (voluntary), SCN-LEVELS
  (commit the levels), SCN-LOAD (the full intake), alongside SCN-WS4c from the base refresh.
  Zero solves, zero code, zero defaults, zero markers.
- 2026-09-06 — **SCN-DESK r#6 → r#9 (main HEAD `0e20e8cf` at r#9).** r#6: all four ruling-released
  lanes landed (WS-1c, WS-2b, LEVELS, LOAD); WS-2b found the CCS emission-rate seam that sign-flips
  NEISO's 2030 CO2 → card D-7 → **S5** (r#6 am.1, the `RULED` line appended to §6 at r#9). r#7: WS-4c
  landed (19 arms, 20 HIT / 3 SPLIT / 3 MISS; the fossil-average heuristic biased; G-DRIFT vindicated)
  and Stage A-LOAD issued; WS-1b-r2's phase 0 killed the desk's own 2026 charter (every RFF path
  anchors at $0 in 2026) — 2027 scope ratified. r#8: A-LOAD running as one six-ISO lane; S4's intake
  re-derived the load constants the pre-declaration chain scored against. r#9: A-LOAD frozen at
  `1cc45bb2` with 0 of 16 legs solved at its last commit (D-5 still not presentable); WS-1b-r2's ERCOT
  2027 pair NOT KILLED with the REF adequacy-collapsed at 2027; **the CCS seam is unchartered on the
  capx queue** (card D-9); SCN-WS3b undispatched three refreshes (card D-8, third stem held). **r#9 am.1: S6 (D-8) relaunch
  now → SCN-WS3b-r3 issued; S7 (D-9) the seam repair named the capx director's next lane, routed.** Zero
  solves, zero code, zero defaults, zero markers, at every refresh.
- 2026-09-07 — **SCN-DESK r#20 (main HEAD `32516df6`).** 51 registered legs: **MISO 13 COMPLETE** (incl. `ces-p60`), ERCOT 11 + FINDING, NYISO 10 (incl. `ces-p60`), NEISO 9 + FINDING, CAISO 8 (incl. `ces-p60`) — **ruling S15 has executed on three ISOs**. **PJM is the one failure and it is the same one for a third refresh: 10 cases solved into `results/`, ZERO registered** (4 → 8 → 10), ~7–8 h of LP invisible to the audit, the collate and the synthesis; not blocked, just handed off by shards to a coordinator that has not run, and closable in one zero-LP session. **Four of six ISOs owe a FINDING** (only ERCOT and NEISO have one), and gate scoring, §5.1 and the matrix cells all hang off them. S17 landed mid-flight — `cap-state-tight` is registered on NEISO/NYISO/CAISO and solved on PJM; per the ruling none is un-registered, all leave the Stage-A synthesis and §5.1, and they become the Stage-B seed. Five close-out/continue prompts issued, no new solve scope, no card. Audit EXIT 0; D-5 still held under S13.
- 2026-09-07 — **SCN-DESK r#19 (main HEAD `10c573b7`).** 37 registered policy legs (ERCOT 11/11 + FINDING, NEISO 9 + FINDING, NYISO 8, MISO 7 **including the campaign's first `ces-p60`, so S15 is executing**, CAISO 2, **PJM 8 solved and STILL ZERO REGISTERED — the gap doubled from r#18**). Two findings outrank the counts: **NEISO refused a charter-ordered kill and was right** — `CAP-STATE-TIGHT` binds in all five years and is a **LOOSENING** of +2.9 to +13.9 Mt, its dual 12.23 → 8.26 $/t below the 26.05 → 34.15 RGGI adder it replaces → card **D-13**, **ruled S17: drop from Stage A, route to Stage B** (S12 not withdrawn; NEISO/NYISO cap legs stay registered but leave the Stage-A synthesis); and **NEISO's entire policy axis is measured invisible to the deployment screen** (`vre_mw` identical in REF and all eight non-cap arms in every year), confirming the S15 mask on solved legs. **ERCOT's control was stale and its own lane caught it** — capx D65-B is LIVE on ERCOT, falsifying the "ERCOT is clean therefore D65-B is inert" premise this desk wrote into P1 of every charter v6; RESOLVE-ERCOT re-solved all three legs and ADDENDUM B re-scores. SPP is a seventh ISO but has no scenario base YAML, so no SCN scope moves. Audit EXIT 0; D-5 still held under S13. Zero solves, zero code, zero defaults, zero markers.
- 2026-09-07 — **SCN-DESK r#18 (main HEAD `96a6c4b3`).** **SCN-WS5A-RESOLVE COMPLETE, 13/13** — headline: the campaign's CO2 levels were overstated by up to 57 % and the repair does not cancel out of the deltas; every leg gated 5/5, 2026/2027 byte-identical to pre-fix. CAISO and MISO closed 3/3, so **CAISO and MISO policy meet P1 and are issued on v6**. Policy running in all four issued ISOs (ERCOT 3/11, PJM 4 legs at 13/13 cases surviving, NEISO 2/9, NYISO REF+LOAD-HI rematerialized). **The refresh's finding, found independently by two lanes and generalized here:** the entry screen's attribute fold is `max(EAC, RPS, clean)` with no fuel gate on the RPS leg, and `STATE_RPS_ACP` (MISO 30, NYISO 40, PJM 45, CAISO 50, NEISO 50, ERCOT absent) sits above the committed CES ladder {10,20,30} and both voluntary ceilings in every ISO — so the CES premium axis cannot discriminate on entry in five of six ISOs, and the one unmasked ISO is the adequacy-collapsed one. Not a defect (rule 19's `max()` doctrine); the retirement leg is fuel-gated, so the legs still solve. Card **D-12** presented and **ruled the same sitting — S15**: add one bracketing `CES-P60` leg above the mask, one common level, never per-ISO. **Governance moved under us and neither act is this desk's:** `complete` widened to {ERCOT, NEISO, PJM, CAISO, NYISO} (only MISO outside), and SPP exists as a seventh matrix shard. D-5 stays held under S13 — the policy half has not landed. Audit EXIT 0. Zero solves, zero code, zero defaults, zero markers.
- 2026-09-06 — **SCN-DESK r#17 (main HEAD `28fb1882`).** **The policy half is live.** SCN-WS5A-POLICY-ERCOT
  launched, pushed its PRECOMMIT before any LP, and killed 2 of 12 cases at zero cost on proven identities
  (`VOL-MID` slack in all five years; `CAP-STATE-TIGHT` resolving to no carbon program at all on ERCOT) — and
  caught **two defects in the charter this desk wrote**: P2 named an in-place REF path when RESOLVE actually
  renames its legs to `…-2026-09-06-r2/<ISO>/<CASE>/`, and G7's `$4.5/MWh` ceiling is the **mid** cell where every
  surviving voluntary leg runs `high` (`$7.0`). Both corrected in **charter v6**, which supersedes v5. RESOLVE
  split into three parallel lanes and stands at 6/13 — the PJM REF landed with all five gates PASS and measured
  the D67-ARM/D81 confound **INERT** (rate-capped backstop at a −16 % reserve margin), so PJM's P1 is met and
  **NEISO / NYISO / PJM are issued on v6**. Card **D-11** presented and **ruled the same sitting — S14**: charter
  P4 relaxed to rule 12's own ~2-concurrent cap, releasing ERCOT's eleven prepared legs to solve alongside RESOLVE.
  Recorded against the desk: r#16's "re-solved in place / accepted deviation" reading of RESOLVE was wrong on
  both halves. Audit EXIT 0. Zero solves, zero code, zero defaults, zero markers.
- 2026-09-06 — **SCN-DESK r#16 (main HEAD `00cee150`).** SCN-WS5A-RESOLVE running: PRECOMMIT (THE PIN `bdfb3095`) + 5/13
  legs, every gate PASS; S5's identity measured on the NEISO/NYISO campaign REFs (NYISO 2030 CO2 −46 %); the cache
  blocker defeated by D65-B's re-key. Policy charter v5: ERCOT / NEISO / NYISO launchable now, PJM / CAISO / MISO
  wait for their REF. Desk's r#14 D67-ARM note corrected (live on PJM). capx D79 fingerprint landed after the pin.
- 2026-09-06 — **SCN-DESK r#15 (main HEAD `e6a0402f`).** Quiet: RESOLVE undispatched a second refresh — asked,
  re-emitted verbatim, not graded lost (owner batches launches); policy lanes correctly unlaunched; capx D79
  (the cache-key fingerprint this desk routed) ruled ADOPT; D65-B-R's batch still holds the per-plant slot.
  No card.
- 2026-09-06 — **SCN-DESK r#14 (main HEAD `5375be8b`).** Quiet: RESOLVE not yet dispatched (asked), policy lanes
  correctly unlaunched, audit EXIT 0; the capx queue is saturated with solves, so rule 12 sequences RESOLVE's
  per-plant legs (charter sentence added). CLAUDE.md +1 (D67-ARM), INERT for every SCN leg. No card.
- 2026-09-06 — **SCN-DESK r#13 (main HEAD `13ee0c89`).** Stage A-LOAD COMPLETE at the frozen pin (16/16, synthesis,
  cost table); ruling S8 never executed (the amendment had no session) → SCN-WS5A-RESOLVE issued with the cache
  blocker defeated. SCN-FIX2 + SCN-CAP landed complete (carbon form committed; CARB-HI live at full horizon on
  NYISO/NEISO; the cap field and case; PJM falls through to the regional budget → policy charter v4). capx D80:
  the audit is EXIT 0 on main. Card D-5 presented with a HOLD recommendation. Zero solves, zero code, zero
  defaults, zero markers.
- 2026-09-06 — **SCN-DESK r#12 (main HEAD `ba894c9c`).** SCN-FIX1 landed items 1–2 (audit 30 → 8; collate
  sign-flip repaired); capx D80 cross-checked the declarations byte-identically; SCN-WS5A-LOAD 12/16 with MISO
  complete and its D-10 scope correction matching r#11; the carbon-form switch never reached FIX1 (issued on an
  unmerged PR) → SCN-FIX2 issued; capx D79 charters the cache-key fingerprint this desk routed. Card D-2(c)
  (CAP-STATE-TIGHT slope + field) presented — **ruled the same sitting (am.1): S12**; SCN-CAP issued and the cap
  case joins the program-ISO policy lanes. Zero solves, zero code, zero defaults, zero markers.
- 2026-09-06 — **SCN-DESK r#11 (main HEAD `d1aa877f`).** Stage A-POLICY RELEASED under S5 (D77's identity gate
  is the paired check); six per-ISO policy charters issued, solves gated on the campaign's post-D77 pin.
  SCN-WS1b-r2 landed complete (12/12). SCN-WS5A-LOAD 11/16: PJM (909.8 MW) and MISO (334.5 MW) carry CCS
  via §45Q with no program, so S8's re-solve set widens to every ISO but ERCOT. capx D65-B re-keyed the
  CCS economics. The carbon FORM still the delta stand-in → SCN-FIX1 re-issued with the YAML switch.
  Cards D-2(b)/D-3c/D-6 presented — **ruled the same sitting (am.1): S9, S10, S11**; the voluntary legs join
  the policy lanes by addendum; SCN-WS3c withdrawn as absorbed. Zero solves, zero code, zero defaults, zero markers.
- 2026-09-06 — **SCN-DESK r#10 (main HEAD `6887484f`).** S7 executed by capx D77 within the hour (repair on
  main, screen owed). SCN-WS3b landed complete (VOL-* cases live and S5-held; ERCOT 2026 T0 slack → WS-3c held
  on a criterion). SCN-WS5A-LOAD 3 of 6 ISOs: falsified S5's premise (state programs arm the retrofit screen;
  NEISO REF 8.8 GW `gas_cc_ccs`), ERCOT REF in deep shortage → card **D-10** (re-pin once post-D77).
  SCN-WS1b-r2 5 of 6 pairs. Main red on the Y-24 forecast-invariant audit (18 of 26 SCN) → SCN-FIX1 issued
  with the collate common-set repair. §5.1 untouched here (WS-1b-r2's open PR #5101 holds the Carbon rows).
  Zero solves, zero code, zero defaults, zero markers.
