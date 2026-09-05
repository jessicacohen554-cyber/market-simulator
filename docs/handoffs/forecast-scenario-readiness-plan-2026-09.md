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
- **G-L2.** No forecast-load loader; every rate is a hand-transcribed cited constant.
  No LTLF / CELT / PJM load forecast / IEPR file is under `data/raw/`; the 2026 Gold Book
  the NYISO row cites is absent (only 2018–2022 on disk). The scenario can run on the
  constants today; a curated `load-forecast` datatype is a provenance upgrade (§3.4,
  owner-gated — Q23's "I'm not getting more data" was an FC-5 ruling, but it signals the
  posture).
- **G-L3 (coherence of the high case).** `demand_growth_path=high` and
  `datacenter_load_path=high` are independent axes; ERCOT `high` DC (122 GW by 2030)
  exceeds the grown energy and drops into the additive tail regime
  (`datacenter.py:318-320`). The high-load scenario needs a *declared* pairing (§3.4).
- **G-L4 (adequacy response).** At `mid` load the T1-F FC-1 fail sets already read
  ERCOT {I12, I3} · CAISO {I12, I3, I7} · PJM {I7, I12} · MISO {I3} (board `gate_reading`,
  2026-09-05). Higher load pushes the same invariants harder: in ERCOT (no backstop) it
  shows up as **unserved-energy slack**, in curve-ON ISOs as backstop gas_ct. A CO2 number
  read under binding slack is understated by the shed energy — WS-0 reports unserved
  energy beside CO2 and WS-4 pre-declares how each ISO's high case is read.
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

### 3.5 The case set (proposed; owner box D-2 sets levels)

`configs/scenario_campaign_matrix.yaml`, `cases:` mode, every case one or two field
overrides on REF. Levels are illustrative until D-2.

| Case | Overrides | Question it answers |
|---|---|---|
| `REF` | — | the reference; the ISO's shipped posture |
| `CARB-LO` / `CARB-MID` / `CARB-HI` | `carbon_price_path: low/mid/high` (floor semantics after WS-1) | price → dispatch re-ordering, CCS, thermal mix, VRE entry via prices, CO2 |
| `CAP-STATE-TIGHT` | `mass_cap_enabled: true` + declining `mass_cap_tons` on program ISOs | price vs quantity instrument comparison |
| `CES-P10` / `CES-P20` / `CES-P30` | `federal_ces_enabled: true`, `federal_ces_premium_usd_per_mwh: 10/20/30` | the uniform-price (tradeable) CES response curve |
| `CES-T80` | `federal_ces_target_by_year: {2026: <current>, 2035: 0.80, 2050: 1.00}`, ACP `<D-2>` | the uniform-share (no-trade) standard; dual = implied EAC price |
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
| 1 expressible in committed config | yes (semantics defect G-C1) | yes | **no** | **no** | partial — **siting sourced** for ERCOT/PJM/MISO (SCN-WS4a), still **no named case** | — |
| 2 reaches dispatch + deployment | yes | yes | **no** | **no** | yes | — |
| 3 paired probe right-signed, per ISO | NEISO only | ERCOT only (July posture) | **no** | **no** | **no** | — |
| 4 backcast byte-identity | yes | yes | — | — | yes | — |
| 5 matrix duty | stamped | stamped | — | — | stamped | — |
| 6 emissions grain | scalar only | scalar only | — | — | scalar only | **G-E1..E5 open** |
| 7 registered probes on dashboard | NEISO FC-6 pair | pruned (G-S5) | — | — | none | — |

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
