# PRECOMMIT — SCN-WS2b: the CES premium ladder re-proved at HEAD posture

**Lane:** SCN-WS2b · **Branch:** `claude/scn-ws2b-ces-clearing-y40sks` · **Date:** 2026-09-06
**Base:** `origin/main` `af6269cf11ffd5953f64a4767277fa8724171d0f`
**Charter:** `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §3 WS-2 items 3–6 / §7 "WS-2b"
**Model:** `claude-opus-5` (rule 27 `[R-PUSH]`: this lane adds `scripts/ces_national_clearing.py`)
**Data profile:** `ercot`, then `neiso` (full clone — every blob local; `hydrate_data.py` is a no-op here)

**Rule 29 `[R-SCREEN]` compliance.** This document is pushed BEFORE the first solve. Nothing in
it is written after a number was seen. Its predictions are falsifiable and its misses will be
reported at full magnitude in the FINDING, per the SCN-WS0 §3.1 precedent.

**Transport note.** The desk's charter names the branch stem
`claude/scn-ws2b-ces-ladder-clearing-p9wf`; this session's harness assigns
`claude/scn-ws2b-ces-clearing-y40sks` and forbids pushing elsewhere. Same lane, same files.

---

## 0. What is being screened, and what is not

**The object under test is the federal CES premium at the HEAD forecast posture.** The July
FF-3B POC (`docs/handoffs/ff-3b-ces-poc-2026-07.md`) proved the machinery carries the signal at
a posture that no longer exists: at least **eight** solve-affecting defaults on the ERCOT
forecast path have moved since (§2). G-S5 pruned the three POC sidecars, so the POC now survives
as a handoff doc only. Item 1 restores the evidence at the current posture.

**Item 1's deliverable is the ATTRIBUTION, not the level.** The direction must hold — that is
the STOP gate (§4). The level will not, and §5 pre-registers which flip is expected to explain
which level change **before the 2030 surface is seen**. That ordering is the whole point: an
attribution written after the surface is narrative, not evidence.

**What this lane does NOT do.** No `ScenarioConfig` field is added; no default moves; no LP row
or objective coefficient changes; `policy/federal_ces.py`, `policy/clean_tiers.py`,
`model/lp/rows.py` and `scenarios.py`'s `federal_ces_*` block are **not touched** (SCN-WS2a is
live in all four). No solve outside this document. No CI workflow.

---

## 1. Phase 0 — zero-LP, run before any solve

Rule 29 clause (0): the pre-solve gate an arm must pass before it reaches an LP.

### 1.1 The credited-column census (computed, not asserted)

`matrix_configs(ercot_ces_poc_2026_2030.yaml, ces_premium_matrix_poc.yaml)` expands to exactly
`{BAU, CES-20, CES-40}`. Resolved at HEAD:

| case | `federal_ces_enabled` | crediting | real escalation | premium $/MWh, every year 2026–2030 |
|---|---|---|---|---|
| BAU | False | `clean_capture` | 0.0 | 0.0 |
| CES-20 | True | `clean_capture` | 0.0 | 20.0 |
| CES-40 | True | `clean_capture` | 0.0 | 40.0 |

The premium is **flat in real terms** — `premium_for_year` returns the same number in all five
years — so any year-over-year movement in the surface is the *fleet* responding, never the
instrument escalating.

`tech_credit_fraction` over the fleet taxonomy at CES-40 (`clean_capture`):

| credit 1.0 | credit 0.95 | credit 0.0 |
|---|---|---|
| wind, solar, nuclear, hydro, geothermal, offshore_wind, hydrogen_ct, hydrogen_ccgt | gas_cc_ccs | gas_cc, gas_ct, gas_st, coal, oil, biomass, battery, demand_response, **import** |

**`import` is a `FUEL_TYPE_MAP` fuel and it is NOT in `federal_ces_eligible_fuels`.** Every
import MWh therefore earns zero CES credit in this model — *including NEISO's firm Hydro-Québec
hydro tranches*, which are zero-carbon by construction (their emission rate is held at 0 in the
LP). This is a **modelling posture, not a defect**, and it is stated here before the solve
because it drives the §6 leakage prediction and is a disclosure item for the campaign either way:
real CES designs generally credit delivered zero-carbon imports, and this one does not.

**Predicted footprint, from this census alone:** the premium is a pure offer-side credit on the
credited columns. It cannot touch a fossil, oil, biomass, battery or import column directly. Any
change in those rows must arrive through the *dispatch* (displacement) or through the
*capacity screens* (entry/retirement), never through the offer of the row itself.

### 1.2 STOP-gate arithmetic available before the solve

At $40/MWh, a credited zero-marginal-cost VRE column's effective offer floor moves from ~$0 to
**−$40/MWh**; a nuclear column at ~$8–10/MWh variable cost moves to ~−$30/MWh. The
dump/negative-price machinery (`dump_cost = max(ε, −min(wind_mc, solar_mc) + ε)`) means the
premium *must* deepen the negative/zero-price epoch count if it does anything at all. A CES-40
arm that shows **zero** additional negative-price hours has not reached the offer stack and is a
dead arm regardless of what its clean share does.

---

## 2. The default-flip census (the G-DRIFT analogue) — declared before the solve

A literal `git diff <july-sha> HEAD` is **not available**: the 2026-08-16 history rewrite
(`docs/FINDING-history-rewrite-2026-08-16.md`) killed every pre-rewrite sha, and the FF-3B doc's
`57ed9fc` / `415df68` are among them. The census below is therefore built from each field's own
**dated provenance comment** in `src/market_sim/config/scenarios.py` and from
`config/iso_configs.py::_ercot_config` / `_neiso_config` — a stronger instrument than a diff for
this question anyway, because it names the ruling behind each flip.

**LIVE on the ERCOT 2026–2030 forecast path, flipped after the July POC:**

| # | field | July POC | HEAD | flipped | ruling |
|---|---|---|---|---|---|
| F1 | `retirement_rule` | `legacy` | `pipeline` | 2026-08-02 | owner D-1, ffr-owner-sitting-2026-08-02 Add. C.1 |
| F2 | `entry_rate_limits` | False | **True** | 2026-08-02 | owner D-2, "ARM BOTH" |
| F3 | `entry_commissioning_lag` | False | **True** | 2026-08-02 | owner D-2, "ARM BOTH" |
| F4 | `net_cone_forward_escalation` | (pre-flip) | `reindex_gross` | 2026-08-02/03 | — |
| F5 | `capacity_screen_unified_lookahead` | False | **True (ERCOT override)** | 2026-08-05 | `_ercot_config.default_scenario_overrides` |
| F6 | `entry_pipeline_aware_signal` | False | **True (ERCOT override)** | 2026-08-05 | " |
| F7 | `vre_procurement_additions_enabled` | False | **True (ERCOT override)** | 2026-08-05 | " |
| F8 | `capacity_screen_scarcity_restoration` | False | **True (ERCOT override)** | 2026-08-07/08 | " |
| F9 | `entry_margin_exhaustion` | False | **True (ERCOT override)** | 2026-08-25/30/31 | " |
| F10 | `entry_forward_reserve_leg` | False | **True (ERCOT override)** | 2026-08-30 | " |
| F11 | `storage_entry_availability_gate` | False | **True** | 2026-08-30/31 | — |
| F12 | `storage_entry_cost_normalized_rank` | False | **True** | 2026-08-30/31 | — |
| F13 | `fossil_announced_exits_enabled` | False | **True** | 2026-09-03 | owner Q30, capx D44 |
| F14 | `ccs_retrofit_capex_co2_scaling` | (field absent) | **True** | 2026-09-05 | owner Q42, capx D60 |

**Declared INERT for this lane, with the reason:**

- `capacity_market_clearing` False and `capacity_market_supply_clearing_by_iso` armed for **PJM
  only** (owner ruling on capx D57, 2026-09-05) — ERCOT is energy-only and NEISO is not armed.
- `miso_rps_compliance_regions`, `entry_vre_zone_selection`, the four `caiso_*` accreditation
  fields, `pjm_accreditation_design_vintage`, `nyiso_requirement_forecast_peak`,
  `neiso_net_icr_requirement` (default False), `locality_capacity_curves`,
  `adequacy_accounting_ratio_dated_net`, `retirement_sector_gate`, `exit_rate_limits` — all
  another ISO's branch or default-off and absent from this lane's recipe.
- `datacenter_load_path` (`mid`), `correlated_forced_outage` (True), `entry_lookahead_reprice`
  (True), `confirmed_exits_enabled` (True) — **unchanged since July**, so the charter's "DC
  posture" candidate is expected to explain **nothing**. Declared here so that a level change
  attributed to it later would be a contradiction, not a convenience.
- `entry_screen_diagnostics` (True on the ERCOT POC base) — pure observability; the config's own
  comment states the fleet outcome is byte-identical.

**Base configs.** ERCOT re-uses the July POC's own base,
`configs/scenarios/ercot_ces_poc_2026_2030.yaml`, so the base file is not a source of drift.
NEISO has no CES POC base; it uses the committed campaign REF
`configs/scenarios/neiso_scenario_base_2026_2030.yaml` (SCN-WS0's file, **read not written**),
which differs from ERCOT's only by the `entry_screen_diagnostics` observability flag. Declared,
not discovered.

---

## 3. The screen — ERCOT, 2026, three arms

**Screen ISO: ERCOT. Screen year: 2026. Arms: BAU, CES-20, CES-40 (`--set end_year=2026`).**

**Why 2026, stated as a constraint rather than a choice.** Rule 29 names the screen year as the
one where the mechanism's own measured footprint is largest — which here would be 2030, since the
premium is flat and the credited fleet accretes. **That year is not solvable on its own.** A
forecast year N is the output of a one-pass capacity evolution seeded by years 1…N−1
(CLAUDE.md "Capacity Evolution"); a `start_year=2030` run would seed 2030 from the *base-year*
fleet and answer a different question. The window's first year is the only solvable single-year
screen, so 2026 is **forced by path dependence, not selected**. It is named here before the
solve either way.

Cost: 3 × ~2.4 min ≈ 7 min of LP (rule 12: ≤ 2 concurrent invocations; years sequential — one
year each here). The screen bundle is a throwaway diagnostic probe: **never registered, never a
keeper, never quoted as a keeper number**, and its year is re-solved inside the 5-year ladder
(rule 29 clause 2).

---

## 4. The STOP gate — structural, and it may only KILL

Five checks. Every one reads a **mechanism**, not a residual. None can promote an arm; none is
gated on whether the surface got closer to July.

| # | check | kills the arm if |
|---|---|---|
| **G1** | **Monotonicity.** `clean_share(BAU) ≤ clean_share(CES-20) ≤ clean_share(CES-40)` | the premium moves the credited share non-monotonically — the offer credit is not reaching the merit order in the direction its own arithmetic requires |
| **G2** | **Credited set only.** The generation increase at CES-40 vs BAU is confined to columns with a non-zero credit fraction (§1.1); no credit-0 column (coal, gas_*, oil, biomass, battery, import) rises *as a share of load* except as displacement arithmetic requires | the premium reaches a column it does not credit — an off-footprint effect the mechanism cannot explain |
| **G3** | **Negative-price sign (July's §6-1).** `negative_price_hours(CES-40) ≥ negative_price_hours(CES-20) ≥ negative_price_hours(BAU)`, and CES-40 > BAU strictly | a $40 credit on zero-MC columns produces no additional negative/zero-price hours — the credit never reached the offer stack (§1.2) |
| **G4** | **Captured-price sign (July's §6-3).** Solar and wind `captured_price_usd_per_mwh` fall monotonically with the premium, and `avg_price_usd_per_mwh` falls with it | self-cannibalization is absent — either the credit is not in the offers or the price is not the dual |
| **G5** | **No non-target load-bearing flip.** No invariant that passes in BAU FAILs in a premium arm *for a reason the premium cannot cause*. The July POC's I3/I12/I14 are known BAU-side ERCOT adequacy failures (F-2) and are **expected in every arm**; I9 (storage ε-degeneracy) is expected to appear **only** under the premium and is a positive machinery signal, not a kill | a premium arm breaks something outside the CES footprint |

**Verdict rule.** All five PASS → spend the 5-year ERCOT ladder, then NEISO. Any one FAILs →
**stop, report the kill as the session's result, and do not spend the remaining years.** A gate
that kills is the deliverable in that case.

**Not in the gate, deliberately:** the *level* of any quantity; its distance from July; whether
2030's clean share is "right". Selecting on those is the fitted-mechanism selection rule 1
`[R-STRUCT]` forbids, done one year at a time.

---

## 5. Pre-registered attribution — which flip explains which level change

Written before the 2030 surface exists. July's ERCOT 2030 surface, for reference:

| metric (2030) | BAU | CES-20 | CES-40 |
|---|---|---|---|
| clean_share | 0.400 | 0.492 | 0.506 |
| negative_price_hours | 0 | 1017 | 1111 |
| avg_price $/MWh | 57.52 | 54.39 | 53.02 |
| solar build GW | 9 | 19 | 20 |
| wind build GW | 5 | 13 | 17 |
| solar captured price $/MWh | 30.02 | 11.89 | 1.36 |
| wind captured price $/MWh | 50.43 | 40.74 | 30.36 |
| premium_capture_rate | 0.801 | 0.877 | 0.872 |

Predicted level changes and the flip each is charged to:

| # | prediction (HEAD vs July) | charged to | why |
|---|---|---|---|
| **P1** | **Solar and wind build GW fall in every arm**, and the *premium-induced increment* (BAU→CES-40) falls proportionally more than the BAU level | **F2 + F3** (`entry_rate_limits`, `entry_commissioning_lag`) | the ladder caps annual build at 2.0× the tech's prior maximum annual build seeded from EIA-860; July's 9→20 GW solar swing is exactly the unconstrained one-year build the ladder exists to stop, and the lag defers what does clear |
| **P2** | **Clean share falls in every arm**, most in the premium arms | **F2 + F3**, via P1 | fewer credited MW online by 2030 ⇒ less credited energy |
| **P3** | **BAU `avg_price` rises** vs July's 57.52 | **F1 + F13** (`retirement_rule=pipeline`, fossil dated exits) | both remove more thermal capacity from the 2026–2030 fleet than the legacy counter did; a thinner stack prices higher |
| **P4** | **The premium's price *delta* (BAU − CES-40) narrows** vs July's −$4.50/MWh | **F2 + F3**, via P1 | cannibalization is driven by *added* VRE; less added VRE ⇒ less price suppression |
| **P5** | **Negative-price hours fall in the premium arms** vs July's 1017 / 1111, but stay strictly > 0 | **F2 + F3**, via P1 | negative-price epochs are a VRE-penetration phenomenon; the credit still floors offers at −$20/−$40 in the hours VRE is marginal, so the count cannot go to zero (this is G3) |
| **P6** | **Captured prices rise** vs July's $1.36 solar / $30.36 wind at CES-40 (i.e. less collapse) | **F2 + F3**, via P1 | the collapse is self-cannibalization; less self to cannibalize |
| **P7** | **Any CCS-credited MWh in 2028–2030 is lower or zero** vs a July-posture counterfactual | **F14** (`ccs_retrofit_capex_co2_scaling`) | D50 measured ERCOT's carbon-0 retrofit screen closing 3.79 GW → 0; ERCOT has no carbon price, so the retrofit channel into `gas_cc_ccs` (the only 0.95-credited class) should be shut. July's report carries no CCS line, so this is a **one-sided** prediction: it can be falsified by a non-zero CCS build at HEAD, not confirmed against a July number |
| **P8** | **`premium_capture_rate` is roughly unchanged** (~0.80 BAU, ~0.87 premium) | **nothing — no flip predicted** | it is a ratio of delivered to potential credited energy; the flips change the *quantity* of credited fleet, not the curtailment fraction it suffers. A large move here is an **unattributed level change** and will be reported as a finding, not explained away |
| **P9** | **DC posture explains nothing** | **nothing** | `datacenter_load_path` is `mid` in both postures (§2) |

**Honesty clause.** Any level change that none of F1–F14 explains will be reported as an
**unattributed level change** — named, quantified, and left unattributed. Per the charter: an
unattributed level change is a finding, not a failure, and burying it is what rule 1 forbids.
Each of P1–P9 is falsifiable and every miss is reported at full magnitude.

---

## 6. NEISO — the leakage line, pre-registered

SCN-WS0 measured that a $25/t carbon adder on NEISO cut modeled in-ISO CO2 by −2.71 Mt while
raising `import_co2_mt_reported` by +1.85 Mt on the single `NYISO_CT_peak` rung — **two thirds of
the headline reduction left the scored basis**. The charter asks whether a clean-attribute
premium leaks the same way. It has never been measured.

**Pre-registered prediction: NO, and for a structural reason, not a magnitude one.**

- A **carbon price** raises the cost of in-ISO fossil. It does not raise the cost of an import
  tranche (the border adder is $0 under the default posture — plan §2.1 G-C2), so the cheapest
  substitute for dear in-ISO gas is *someone else's gas across the seam*. Leakage is the
  mechanism working as specified.
- A **CES premium** lowers the effective offer of in-ISO credited columns. It leaves in-ISO
  fossil cost **and** import tranche cost untouched, so it changes the fossil-vs-import ordering
  not at all. What it does is push credited in-ISO clean *below* both — which reduces residual
  demand for fossil and imports **together**.

**Therefore: `import_co2_mt_reported` should be flat or FALL in the NEISO premium arms, and
imported TWh should be flat or fall.** A rise would mean the premium is displacing something
that was itself displacing imports, and I would not currently be able to explain it — it would
be reported as an unexplained result.

**The asymmetry that keeps this honest, declared up front (§1.1):** NEISO's zero-carbon firm HQ
hydro imports earn **no** CES credit in this model. So the premium is, in NEISO specifically, a
subsidy to in-ISO clean generation *against* an uncredited zero-carbon import — which biases the
prediction toward imports falling. That is a property of the crediting posture, and the FINDING
will say so beside the number rather than presenting the result as a clean win.

`import_co2_mt_reported` and `import_co2_basis` will be reported beside `emissions_mt` for
**every** NEISO leg, per the charter.

---

## 7. Item 2 — `scripts/ces_national_clearing.py` (zero-solve), declared

Built and tested **unconditionally**, independent of the ladder's outcome.

- **Input:** a campaign's committed premium legs (per-ISO, per-year `clean_share` and load).
- **Method:** interpolate each ISO's clean-share-vs-premium curve; solve for the **uniform
  premium** at which `Σ_ISO credited MWh ≥ target × Σ_ISO load`, per year.
- **Output:** that premium, the per-ISO clean shares at it, and — **beside** it — the per-ISO
  target-row result from SCN-WS2a. The two bracket the cross-ISO-trade question (G-S2): uniform
  price = unconstrained credit trade; uniform share = no trade. The spread is the answer's
  uncertainty and is reported as such.
- **Tests:** synthetic curves with known closed-form answers — monotone, saturating, flat, and
  a non-crossing (target unreachable at any premium) case.
- **Declared limitation.** SCN-WS2a's target-row probe has **not landed** at the time of writing.
  If it has not landed when this lane finishes, the script emits the uniform-price answer alone,
  leaves the comparison column **empty with an explicit note**, and the FINDING says the bracket
  closes when WS-2a lands. **The other side of the bracket will not be invented.**

---

## 8. Owner box D-2 is OPEN

The `{10, 20, 30}` premium ladder stands from D8 and the POC's `{20, 40}` is the July instrument.
Both are used exactly as the charter names them. Any premium or national target level this
session chooses itself (the clearing script's demonstration target) is labelled **illustrative**
and is never presented as a campaign parameter.

---

## 9. Budget and discipline

- ERCOT ~2.4 min/solve-year, NEISO ~1.5 (FF §2.4). Screen 3 years; ERCOT ladder 15; NEISO ladder
  15 ⇒ ~33 solve-years, ~70 min of LP.
- Rule 12: **years sequential within an invocation, always**; ≤ 2 concurrent invocations;
  `run_ces_leg.py` is one leg per invocation by design. Solves run in-session, never on a CI
  runner.
- Wall and peak RSS per solve-year go in the FINDING.
- Matrix: the ERCOT and NEISO `federal_ces_enabled` cells are re-stamped as the **LAST commit**,
  after `git fetch origin main` + rebase, one line each (desk ledger §4 protocol item 2/3a).
- Any edit outside this lane's declared regions is a **STOP**, routed to SCN-DESK in the FINDING.
