# Forecast Driver & Capacity-Revenue Validation Plan — 2026-07

**Purpose.** (1) Audit how well-equipped the model is to *forecast* — are the
variables/parameters we feed it (carbon price, fuel paths, load growth, tech
costs, IRA, RPS) wired end-to-end and do they respond the way production-cost
and capacity-expansion modeling practice says they should? (2) Define how
capacity revenue is (and should be) accounted for in the capacity-market ISOs
(PJM/MISO/NYISO/NEISO/CAISO-RA) for capacity-expansion and retirement modeling.
(3) Deliver the test program, the data needs, and a session prompt pack with
model assignments and an explicit parallel-vs-sequential schedule.

**Method.** Three code sweeps (capacity/screens, driver parameterization,
testing/validation infra) verified against `origin/main` 2026-07-11, reconciled
with the standing program docs. **This plan builds on, and does not duplicate:**

- `docs/forecast-validation-plan.md` + `docs/handoffs/forecast-validation-program-2026-07.md`
  — hindcast harness, invariant suite I1–I14 / P1–P3, golden bands (built; §2 below
  reports their status honestly).
- `docs/handoffs/capacity-economics-plan-2026-07.md` (W2-P3) — FOM/floor/foresight/DC
  block; Stage 1–3 executed; **FOM flip still blocked on the scarcity-revenue side**.
- `docs/forecasting-entry-exit-assessment.md` — the ERCOT net-revenue reconciliation
  (peaker/storage revenue ~1–6 % of the Potomac PNM benchmark at time of writing).
- `docs/forecast-methodology-gaps-2026-06.md` + `docs/gap-register-2026-07.md`
  (G-20/G-22 AS co-opt lane; G-30/G-37/G-41/G-42 forecast-side rows; #1532 FPR flag).

All work below obeys the CLAUDE.md rules: forecast probes never register on the
backcast dashboard; no solve or scoring touches 2022/H1-2026 (rule 22); published
market-design parameters (demand curves, net-CONE, ELCC curves) are admissible
inputs and published auction outcomes are **validation observables — compare,
never pin, never fit** (rules 1/13); every new tunable lands in
`ScenarioConfig`/`constants.py` with a citation (rules 5/24).

---

## 1. Audit scorecard — model vs. commercial practice

Reference frame: what commercial production-cost tools (PLEXOS, Aurora, EnCompass,
PROMOD) and capacity-expansion frameworks (Aurora/EnCompass LT, PLEXOS LT, NREL
ReEDS, EPA IPM, EIA NEMS/EMM, Astrapé SERVM for RA) do for each driver, vs. what
this repo does today. Verdicts: **STRONG** (at or above commercial practice),
**ADEQUATE** (workable, known refinements), **GAP** (below practice, plan item),
**UNTESTED** (built but behavior never measured).

| # | Driver / mechanism | Repo today (verified anchors) | Commercial practice | Verdict |
|---|---|---|---|---|
| D1 | **Carbon pricing** | Exogenous RFF scalar paths (`CARBON_PRICE_PATHS`, `constants.py:1573`) into MC at `fleet.py:3447`; RGGI/CARB adders with measured 2023–25 anchors + floor-band escalators (`cap_and_trade.py:146-164`); opt-in mass-cap **LP row** whose dual is an endogenous allowance price (`mass_cap_enabled`, `cap_and_trade.py:216`); CARB unspecified-import border adjustment (`constants.py:1648`) | Exogenous allowance paths (Aurora/PLEXOS) or endogenous cap duals (IPM) — repo has **both**, which is above most production-cost setups | **ADEQUATE / UNTESTED** — plumbing is good; no test anywhere verifies coal→gas switching or CO₂ monotonicity on a real solve per-PR (weekly cron only); `carbon_program_price_path` declared but unwired (`scenarios.py:122`); PJM RGGI inert (no budget); "rollback" bundle is a freeze proxy |
| D2 | **Fuel prices** | AEO2025 Henry Hub trajectories hardcoded with a standing **TODO: verify vs AEO Table 13** (`constants.py:914,927`); ISO basis constants; last-YoY-ratio extrapolation beyond table (`fuel.py:178-181`); coal flat 1 %/yr escalation (`constants.py:1225`); oil/biomass flat scalars; **nuclear fuel = $0** (`fuel.py:113-115`); PB-2 gas shock is a single persistent lognormal level | Near-term market forwards blended into fundamental long-term (AEO/consultant curves); full-fuel coverage incl. uranium | **GAP** — no AEO data file on disk (values hand-typed), no forward-curve hookup, no coal/oil paths, no uranium |
| D3 | **Load growth** | Two-era scalar per ISO (`DEMAND_GROWTH_RATES`, transition 2030) compounded onto one weather-year shape (`runner.py:238`); additive data-center block (built, W2-P3) but **MISO/NEISO DC tables empty** (`constants.py:877`); no electrification shape decomposition (documented limitation) | ISO-forecast-anchored energy+peak decomposition; explicit large-load/DC scenarios; end-use electrification reshaping | **ADEQUATE** near-term / **GAP** on DC coverage + electrification shape |
| D4 | **Technology costs / WACC** | ATB 2024 values hardcoded (`NEW_ENTRY_COSTS`, `constants.py:2541`); cost decline via Wright's-Law on hardcoded global deployment (`capacity.py:1624`, `constants.py:2816`) — **no calendar-year ATB decline**; single `nominal_discount_rate=0.08`, needs-citation (`scenarios.py:231`) | ATB-vintage capex-by-year trajectories; tech-differentiated financing (ATB financial cases) | **GAP** (data file + calendar path); WACC differentiation already adjudicated DOCUMENT-AS-LIMITATION (capacity-economics plan §6) — stands |
| D5 | **IRA** | PTC/ITC/45V/45Q with OBBBA cliff years as `ScenarioConfig` fields (`scenarios.py:348-365`; `ira.py`); policy bundles shift cliffs coherently | Full credit stack incl. §45U existing-nuclear PTC and 45Y/48E tech-neutral successors | **GAP (bounded)** — **no §45U** (nuclear retirement screens see only exogenous ZEC/EAC), no 45Y/48E semantics |
| D6 | **RPS / CES** | Annual LP constraint, dual = REC price, ACP escape column caps the dual (`STATE_RPS_FLOORS`/`STATE_RPS_ACP`); nuclear excluded from the retirement-screen credit (CX-6a half landed), **`_build_rps_row` half deferred** | RPS as constraint with ACP ceiling is exactly right | **ADEQUATE** — finish CX-6a row half; no PJM RPS floor entry |
| D7 | **Capacity revenue (capacity-market ISOs)** | Fixed exogenous net-CONE × (1−EFORd), same $ for every qualifying MW (`capacity_revenue_per_mw_yr`, `capacity.py:601-623`; `MARKET_DESIGN`, `constants.py:2079-2113`); consumed by retirement (`capacity.py:1255`), thermal entry (`:2073`), storage entry (`storage.py:843-875`); binary long-zone zeroing gated default-off; **no sloped VRR demand curve, no clearing, no forward lag, no seasonal, no CP/PAI**; flat VRE ELCC (wind 0.16 / solar 0.18, `constants.py:2198`) that never declines with penetration; storage ELCC does decline (duration curve + saturation + dilution); ICAP→UCAP ratio only on the requirement side; **no capacity revenue in `plant_financials.py`** | Net-CONE-anchored sloped demand curves (PJM VRR, NYISO ICAP curve, ISO-NE MRI, MISO seasonal PRA curve); clearing from accredited supply vs curve; marginal-ELCC accreditation declining with penetration; long-run equilibrium price → net-CONE of marginal entrant | **GAP — the centerpiece of this plan (§3)** |
| D8 | **ERCOT (energy-only) adequacy revenue** | ORDC scarcity adder + growing endogenous AS co-opt (G-38 done, G-20/G-22 open); retirement/entry screens use attainable pro-forma margin incl. reserve price (Stage-2 fix); but the joint-protocol audit measured screen CT revenue **17 $/kW-yr vs Potomac SOM ≈ 68** and the FOM flip is blocked on it | Scarcity-rent calibration to SOM/PNM benchmarks; reserve-margin backstop | **GAP (owned by G-20/W22 lane)** — this plan adds the recurring SOM-benchmark check, not a new mechanism |
| D9 | **Scenario/uncertainty machinery** | Deterministic 13-case matrix (`matrix.py`), PB-2 correlated sampler (`uncertainty.py`), PB-3 structural prior, weather ensemble (`ensemble.py`) | Scenario matrices + stochastic draws | **STRONG** — but **no matrix/sweep run has ever been persisted for a forecast horizon** |
| D10 | **Validation infrastructure** | Invariant checker I1–I14 + paired directional P1–P3 (real solves **weekly cron only**); capacity hindcast (ERCOT+PJM 2021–25) built and scored — **large misses** (ERCOT 0 GW solar built vs 25 GW actual; PJM thermal retirements −63 %); golden fixture 2026–2032; **no full 2026–2050 run has ever executed**; F1/F2 (reliability floor / reserve margin de-firming) open; forecast/backcast parity (D-5, CAISO RA floor in `run_calibration.py` but not `runner.py`) ungated | Hindcast + cross-model benchmark + directional tornado as release gates | **GAP — measurement exists, execution and gating don't** |

**One-line verdict.** The model's *driver plumbing* is near commercial grade
(carbon is genuinely good; scenario machinery is above grade), but (a) forecast
behavior is **asserted, not measured** — real-LP directional checks run weekly
at best, the full horizon has never been solved, and the one scored hindcast
missed badly; and (b) capacity revenue is a **fixed-price stub** — fine as a
first-order screen input, structurally wrong for expansion/retirement dynamics
in the five capacity-market ISOs because the price never responds to the fleet.
The two failure modes compound: an entry/retirement loop driven by a
non-responsive capacity price cannot equilibrate, which is consistent with the
hindcast's simultaneous under-build and mis-retirement.

---

## 2. What "performing as expected" means — the test battery

Three tiers. Tier 1 is cheap and runs first (it is the measurement rig for
everything else); Tier 2 requires the §3 capacity-market build; Tier 3 is the
external-benchmark layer. Every expectation below is **pre-registered here**
(before the runs), so results can't be graded on vibes. A directional FAIL is a
root-cause issue to open, never a threshold to widen (rules 1/11/14).

### Tier 1 — Single-driver directional & elasticity ladders (forecast probes)

Config: ERCOT + PJM (the energy-only and capacity-market archetypes), forecast
2026–2030, legacy heat-rate bins for runtime (documented fidelity trade, same as
the tornado), sequential years, ≤2 concurrent invocations (rule 12). Each ladder
varies exactly one driver. Deliverable: `docs/handoffs/driver-battery-<date>.md`
+ JSON, tornado-style.

| Test | Ladder | Pre-registered expectation (PASS criteria) |
|---|---|---|
| T1.1 carbon monotonicity | `carbon_price` ∈ {0, 25, 50, 100} $/t | Coal generation and system CO₂ **strictly monotone ↓**; gas-CC share ↑ then flat/↓; load-weighted price ↑ by ≈ marginal-unit emission rate × Δprice in gas-marginal hours (0.37–0.45 t/MWh × Δ$ band); coal→gas switching concentrated in the $15–40/t range at mid gas (the SRMC crossover computed analytically from the fleet's own heat rates — assert the crossover, not a magic number) |
| T1.2 adder/cap duality | `mass_cap_enabled` with `mass_cap_tons` set to the emissions realized at carbon_price=25 | Binding-cap dual ≈ $25 ± solver tolerance band; slack cap → dual = 0. This is the strongest internal-consistency check the carbon stack has |
| T1.3 gas ladder | `gas_price_factor` ∈ {0.5, 1.0, 1.5} | Implied market heat rate ↓ as gas ↑ (efficient units set price more); coal dispatch ↑ with gas; price level in gas-marginal hours ≈ HR×gas+VOM within band; P2 merit-sign invariant generalized to 3 points |
| T1.4 load ladder | `demand_growth_path` low/mid/high | Scarcity hours, entry GW, and backstop MW all monotone ↑; reserve margin monotone ↓ pre-entry. Also re-run with `datacenter_load_path` mid vs an energy-equivalent uniform scalar: DC block must produce **lower peak growth and higher off-peak net load** (the W2-P3 §4.4 signature) |
| T1.5 IRA cliffs | Build years straddling `ira_wind_solar_last_year` | Wind/solar entry economics show a discontinuity at the cliff; wind dispatch MC is negative pre-cliff (PTC) and ≥0 after; storage entry responds to ITC toggle |
| T1.6 RPS/ACP | NEISO or CAISO forecast, VRE fleet held short vs long | REC dual ≤ ACP always; dual → ACP when physically short, → 0 as VRE builds through the target; nuclear does not move the dual (once the CX-6a row half lands) |
| T1.7 capacity-revenue scalar | PJM `net_cone_per_kw_yr` × {0, 1, 2} | Thermal retirements monotone ↓ in net-CONE; entry GW monotone ↑; ERCOT byte-identical across the ladder (capacity_market=False — a negative control) |
| T1.8 tech-cost path | `tech_cost_path` low/mid/high | Entry mix shifts toward the cheapened tech; cumulative builds monotone; no cobweb (I13 holds on every rung) |
| T1.9 ELCC saturation | Storage fleet seeded at {5, 15, 25} GW (ERCOT) | Storage capacity value per MW monotone ↓; entry tilts to longer duration as penetration rises (duration-ELCC curve doing its job) |

Magnitude cross-checks (report-only, not gates, first round): CO₂-vs-carbon-price
slope against published RGGI/IPM elasticities; implied-heat-rate response against
PJM/ERCOT historical gas-price years. These become gates only after a baseline
round establishes the model's own bands.

**Harness note.** P1–P3 of the invariant suite already implement carbon/gas
directional checks as *paired* runs; Tier 1 generalizes them to ladders, adds
T1.2/T1.5–T1.9, and — critically — **promotes a fast subset to per-PR CI** (a
1-gen/1-zone/24-h analytic LP asserting carbon monotonicity, merit sign, REC≤ACP,
and net-CONE monotonicity — seconds, not minutes; testing-pattern rule) so
directionality can never silently regress between weekly crons again.

### Tier 2 — Capacity-market equilibrium tests (needs §3 CR-1)

| Test | Expectation |
|---|---|
| T2.1 price-to-curve consistency | Clearing price equals the VRR curve evaluated at the model's accredited reserve margin, every ISO-year (arithmetic identity test) |
| T2.2 long-run equilibrium | Multi-decade run: capacity price oscillates around (not diverges from) net-CONE of the marginal entrant; time-average within a band of net-CONE — the textbook equilibrium property fixed-price stubs cannot exhibit |
| T2.3 entry/exit hysteresis | Price above net-CONE → entry next year(s); below going-forward cost → exits; no retire-and-reenter (I5); no full-cap/zero sawtooth (I13) |
| T2.4 saturation | Exogenously overbuild +10 GW: capacity price collapses along the curve; entry stops; retirements resume — the response the current binary `_zone_is_long` gate only crudely approximates |
| T2.5 scarcity substitution (ERCOT) | Same overbuild in ERCOT expresses through ORDC/AS revenue collapse instead — verifies the two market designs produce the same *direction* of adequacy signal through their own mechanisms |

### Tier 3 — External benchmarks (validation observables — compare, never pin)

| Test | Benchmark | Governance |
|---|---|---|
| T3.1 capacity-price reconstruction | Feed each capacity-market ISO's *actual* historical reserve-margin/accreditation position (published auction planning parameters) through the implemented curve; compare with published clearing prices (PJM BRA incl. the 2025/26–2026/27 spike, NYISO spot, ISO-NE FCA/MRI era, MISO seasonal PRA 2023/24+) | Uses published parameters + outcomes for **delivery years ≤ 2025/26**; a comparison table, no fitting; H1-2026-delivery auction rows excluded from any scored metric until markers exist |
| T3.2 SOM net-revenue check (recurring) | Screen revenue stack per class/year vs Potomac/IMM SOM net-revenue tables (ERCOT PNM; PJM/MISO/NYISO/ISO-NE SOM equivalents) — institutionalizes the capacity-economics plan §5 step-1 audit as a standing per-release check | In-sample years only; comparison only |
| T3.3 cross-model corridor | Frozen-config 2026–2035 vs EIA AEO2026 regional capacity/generation, NREL Standard Scenarios mid case, ISO planning outlooks (ERCOT CDR, PJM load forecast) — each material divergence gets a one-paragraph ours-vs-theirs explanation, not a retune | Forecast-mode, unrestricted |
| T3.4 hindcast improvement | Re-score the ERCOT/PJM 2021–25 capacity hindcast after CR-1 + the driver fixes land; extend hindcasts to MISO/NYISO/NEISO/CAISO | Existing harness; hindcast years are in-train |

---

## 3. Capacity revenue in capacity-market ISOs — the plan

### 3.1 Current state (one paragraph)

`capacity_revenue_per_mw_yr(iso, eford)` returns `net_cone × 1000 × (1−EFORd)`
from a two-field `MarketDesign` registry (CAISO 90 / PJM 100 / NYISO 110 /
NEISO 95 / MISO 80 $/kW-yr; ERCOT 0). Every qualifying MW in a
capacity-market ISO earns that fixed price in the retirement, thermal-entry,
and storage-entry screens regardless of how long or short the fleet is; the
only supply response is the default-off binary deliverability gate and the
storage-specific saturation derates. The code itself flags the refinement
("BRA/auction clearing prices can refine it later", `capacity.py:617`).

### 3.2 Target design — CR-1: reserve-margin-indexed sloped demand curve

> **STATUS — CR-1 IMPLEMENTED, default-off (P-1B, 2026-07-11).** The mechanism
> below is landed: `MarketDesign` (`config/constants.py`) grew the normalized
> `demand_curve` points + published `net_cone_curve_per_kw_yr` + citation fields
> for PJM/NYISO/ISO-NE/MISO (CAISO keeps the fixed proxy, re-cited to CPM/CPUC-RA),
> reconciled against the P-0B `capacity-market-demand-curve` datatype in
> `tests/test_capacity_demand_curve.py`. The shared seam is
> `MarketDesign.capacity_price_per_firm_mw_yr`; the reserve position is
> `capacity_reserve_position` (reusing `resolve_adequacy_requirement_mw` +
> `accredited_firm_capacity_mw` — one requirement, one basis), computed once by the
> runner and threaded into all three screens (retirement, thermal entry, storage
> entry). Gate `ScenarioConfig.capacity_market_clearing` defaults **off** and is
> proven byte-identical. Capacity revenue (fixed/curve, labeled) added to
> `results/plant_financials.py`. Methodology spec §5.9 documents it. **No default
> flip this session** — that is gated on P-2A (CR-2). Open first-order items for
> CR-2/CR-3: MISO's RBDC shape reserve positions are representative (only its CONE
> levels are data-derived); NYISO/ISO-NE are modeled annually (seasonal in CR-3);
> the `plant_financials` report path supplies no live reserve position, so it
> reports fixed-mode capacity revenue.

Replace the fixed price with the mechanism the real markets use: a published,
net-CONE-anchored **sloped capacity demand curve** evaluated at the model's own
accredited position. Structural (rule 1), zero fitted parameters (rule 13 —
every input is a published market-design parameter or an existing model
quantity), forecast-mode only (backcast has no capacity evolution).

```
reserve_pos   = accredited_firm_capacity_mw / requirement_mw        # both already computed
capacity_price = VRR_iso(reserve_pos) × net_cone_iso                 # piecewise-linear, published points
```

- **PJM**: VRR curve points (price cap ≈ 1.5–1.75 × net-CONE at requirement−…,
  net-CONE anchor, zero-cross above requirement) from the current BRA planning
  parameters. **NYISO**: ICAP demand curve (zero-crossing at 112 %+ of
  requirement, monthly spot — model annually). **ISO-NE**: MRI-era downward
  slope approximated piecewise-linear from FCA parameters. **MISO**: seasonal
  PRA reliability-based demand curve (introduced 2025/26) — model annual first,
  seasonal in CR-3. **CAISO**: no central auction — bilateral RA; keep the
  current fixed proxy but re-cite it to published CPM soft-offer cap / CPUC RA
  price reports, and mark it the documented low-fidelity member of the registry.
- The curve **replaces** the fixed price in all three screens through the same
  `capacity_revenue_per_mw_yr` seam (one mechanism, rule 19); `MarketDesign`
  grows curve points + citation fields; the fixed net-CONE remains the fallback
  when no curve is published.
- Gate: `capacity_market_clearing: bool` (default **off** until T3.1 validates;
  flipping is a dedicated, cited commit per the W2-P3 convention).
- Also: add capacity revenue to `results/plant_financials.py` (currently absent
  even where the screens pay it), labeled by source (curve vs fixed).

**Explicitly out of scope for CR-1** (documented, revisit on evidence): full
supply-curve auction clearing with unit-level offers (the demand-curve-at-
accredited-position form is the standard capacity-expansion simplification —
ReEDS/IPM-class), CP/PAI performance penalties, forward-period (Y-3) lag,
locational LDA-specific curves (composes later with
`capacity_deliverability_limits` part (b)).

### 3.3 CR-2: validate against auction history (T3.1)

Before any default flip: reconstruct historical clearing prices from published
reserve-margin positions through the implemented curves. Acceptance is
directional + order-of-magnitude (the curve mechanism, parameters as published,
reproduces the observed price *regime* — e.g., PJM's collapse-then-spike across
2024/25 → 2025/26 BRAs), NOT a fitted match. Any residual is documented; the
curve parameters are never bent to close it (they are published instruments —
bending them is rule-23 forbidden).

### 3.4 CR-3: accreditation upgrades (ordered by materiality)

1. **Marginal-ELCC curves for wind/solar** replacing the flat 0.16/0.18 —
   penetration-indexed piecewise curves digitized from published ISO ELCC
   studies (PJM/MISO/NYISO ELCC filings; ERCOT seasonal-rating basis stays).
   This is the missing feedback that lets VRE saturate its own capacity value.
2. **FPR / ICAP-UCAP basis reconciliation** — resolve the #1532 open flag (the
   published FPR embeds ~77 % marginal-ELCC vs the model's (1−EFORd) ≈ 0.92
   basis; sign-flip risk on net-new-entry payoff). Adjudication memo first,
   then one basis everywhere (rule 19).
3. **Seasonal split** (MISO PRA, PJM winter accreditation) — only after annual
   CR-1/CR-2 are validated.
4. **Forward-period lag** (PJM/ISO-NE clear Y-3) — evaluate in the same A/B
   harness the foresight work used; the myopia adjudication memo's caution
   applies (a lag interacts with one-pass evolution; measure, don't assume).

### 3.5 ERCOT stays energy-only — and keeps its own benchmark

No capacity payment for ERCOT (correct). Its adequacy-revenue fidelity is owned
by the AS co-opt lane (G-20/G-22/W22) and gated by the capacity-economics plan
§5 protocol. This plan's contribution is T2.5 + the recurring T3.2 SOM/PNM
check so the "screens collect ~25 % of SOM" gap stays measured every release
instead of re-discovered.

---

## 4. Data needs

Storage per the `data-intake` skill (schema-first, `data/raw/` immutable,
citations into `parameter-citations.md`). "Fetch" = Sonnet session over the
proxy; **anything ERCOT-MIS-hosted is presumed credential-blocked** (precedent:
NP6 HSL intake, `docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`).

| # | Dataset | For | Source | Fetchability |
|---|---|---|---|---|
| N1 | PJM BRA planning parameters (VRR points, net-CONE, IRM, ELCC class ratings) + BRA clearing-price history | CR-1/CR-2, T3.1 | pjm.com capacity-market pages (public XLS/PDF) | **Fetch** |
| N2 | NYISO ICAP demand-curve parameters + spot auction results | CR-1/CR-2 | nyiso.com ICAP pages, demand-curve reset filings | **Fetch** |
| N3 | ISO-NE FCA/MRI parameters + FCA clearing history | CR-1/CR-2 | iso-ne.com (public) | **Fetch** |
| N4 | MISO PRA seasonal clearing history + reliability-based demand curve parameters | CR-1/CR-2 | misoenergy.org PRA results (public) | **Fetch** (some filings via FERC eLibrary — slower but public) |
| N5 | CPUC RA report (bilateral RA prices) + CAISO CPM soft-offer cap | CAISO proxy re-cite | cpuc.ca.gov annual RA report | **Fetch** |
| N6 | ISO ELCC studies (PJM ELCC class ratings, MISO wind/solar ELCC, NYISO/ISO-NE equivalents) | CR-3 curves | ISO planning pages | **Fetch** |
| N7 | EIA AEO2025 price tables (gas, coal, oil) as data files | D2 fix — replace hand-typed constants; resolves the standing TODO at `constants.py:914` | EIA API v2 / AEO table browser | **Fetch** (API key may be needed — free registration; flag if blocked) |
| N8 | NREL ATB 2024 (and 2025 when out) workbook/CSV | D4 — calendar-year capex trajectories | NREL ATB data portal (OEDI CSV) | **Fetch** |
| N9 | Potomac/IMM SOM net-revenue tables (ERCOT, MISO; Monitoring Analytics for PJM; NYISO/ISO-NE SOM) | T3.2 recurring check | monitor sites (public PDFs) | **Fetch** (PDF table extraction — budget time) |
| N10 | RGGI + CARB (CCA) auction results & current program parameters | D1 anchors refresh | rggi.org / CARB quarterly summaries | **Fetch** |
| N11 | EIA uranium marketing annual (nuclear fuel $/MMBtu) | D2 — nuclear fuel ≠ $0 | eia.gov | **Fetch** |
| N12 | MISO/NEISO data-center load decompositions (if now published) | D3 — empty DC tables | ISO load forecast reports | **Fetch; may be MANUAL/absent** — ship 0 where unpublished (never invent) |
| N13 | Gas forward strips (NYMEX HH settle, basis) for near-term blend | D2 stretch | CME settles public but scrape-hostile; broker data paywalled | **MANUAL (owner)** — optional; AEO-only is defensible if documented |
| N14 | NREL Standard Scenarios + AEO2026 regional capacity (when released) | T3.3 corridor | NREL/EIA | **Fetch** (AEO2026 timing dependent) |
| N15 | 45U/45Y/48E statute parameters as enacted post-OBBBA | D5 | IRS guidance / statute text | **Fetch** |

---

## 5. Order of operations

```
WAVE 0 (parallel, ~independent):
  P-0A [OPUS]   Driver-battery harness + per-PR directional smoke      ─┐
  P-0B [SONNET] Capacity-market data intake (N1–N6)                     ├─ no cross-deps
  P-0C [SONNET] AEO/ATB/uranium/RGGI-CARB data intake (N7–N11, N15)    ─┘

WAVE 1 (starts when its own Wave-0 dep lands):
  P-1A [SONNET] Run Tier-1 ladders (needs P-0A)            — findings only
  P-1B [OPUS]   CR-1 sloped demand curve (needs P-0B)      — default-off
  P-1C [SONNET] IRA §45U + 45Y/48E (needs P-0C/N15)         ─┐ parallel with
  P-1D [SONNET] Driver completeness batch (needs P-0C):     ─┘ P-1A/P-1B
                AEO-file wiring, coal/oil paths, uranium,
                carbon_program_price_path, PJM RGGI budget option, DC tables

WAVE 2 (sequential after Wave 1):
  P-2A [OPUS]   CR-2 validation vs auction history (needs P-1B + P-0B) ⛔ gate
  P-2B [FABLE]  FPR/ICAP-UCAP basis adjudication memo (needs P-2A read)
  P-2C [OPUS]   CR-3.1 marginal-ELCC curves (needs P-2B decision + N6)

WAVE 3 (after Waves 1–2; compute-heavy):
  P-3A [SONNET] First full-horizon 2026–2050 runs, all 6 ISOs + invariants ⛔ gate
  P-3B [SONNET] Tier-2 equilibrium battery (needs P-1B default decision + P-3A)
  P-3C [FABLE]  Cross-model corridor report (T3.3) + updated fitness verdict
  P-3D [OPUS]   Hindcast re-score + extend to remaining ISOs (T3.4)
```

**Parallel vs sequential, explicitly:** P-0A/P-0B/P-0C are three independent
sessions — run simultaneously. P-1A/P-1B/P-1C/P-1D can all run in parallel
*with each other* (disjoint files: harness/runs vs `capacity.py` vs `ira.py` vs
`fuel.py`+`constants.py` tables — P-1B and P-1D both touch `constants.py`, so
land P-1D's table additions in separate constants sections or sequence their
merges). Wave 2 is strictly sequential (validation → adjudication → accreditation).
P-3A/P-3B/P-3C/P-3D parallel as sessions but each obeys rule 12 inside
(sequential years; ≤2 concurrent ISO invocations). Compute sessions (P-1A, P-3A,
P-3B) are Sonnet: they run scripted probes, not design work.

**Standing constraints for every session:** no solve/score of 2022 or H1-2026
(rule 22; NEISO's marker doesn't change this plan — none of these sessions
score holdouts); forecast probes go in `docs/handoffs/` reports, never on the
backcast dashboard; any backcast bundle a session *does* produce follows rules
15/16; push via `mcp__github__push_files` only.

---

## 6. Prompt pack

Paste-ready; one prompt per session (keeps diffs reviewable). `[MODEL]` prefix =
assigned model. ⛔ = gate: don't start dependents until it lands green.

### P-0A [OPUS] — Driver-battery harness + per-PR directional smoke

```
[OPUS] P-0A — Build the driver-response battery + per-PR directional smoke tests

Read CLAUDE.md, then docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md
(THE PLAN — §2 Tier 1 is your spec), then docs/handoffs/forecast-validation-program-2026-07.md
§2 (the invariant suite you are extending, NOT duplicating). Fresh branch off latest origin/main.

Deliverables:
1. scripts/run_driver_battery.py: generalizes the existing paired invariants P1–P3 into
   single-driver LADDERS per plan §2 Tier 1 (T1.1 carbon {0,25,50,100}, T1.2 adder/cap
   duality, T1.3 gas {0.5,1.0,1.5}, T1.4 load low/mid/high + DC-vs-scalar signature,
   T1.5 IRA cliff, T1.6 RPS/ACP, T1.7 net-CONE {0,1,2}× incl. ERCOT negative control,
   T1.8 tech-cost, T1.9 storage-ELCC saturation). Reuse the invariant checker's ledger/
   result plumbing and the tornado's report style (markdown + JSON with pre-registered
   PASS/FAIL per expectation). Expectations live in a dataclass table at the top, each
   carrying its plan §2 test id — no scattered literals. ERCOT+PJM, 2026–2030, legacy
   bins, sequential years, ≤2 concurrent invocations (rule 12). Each ladder is
   resumable/cacheable (check-before-run, rule 7).
2. Per-PR fast smoke: tests/test_driver_directionality.py — 1-gen(+1 coal +1 CC)/1-zone/
   24-hour analytic LPs asserting on REAL solves (seconds): carbon monotonicity + the
   analytic coal/gas SRMC crossover, merit sign under a gas move, REC dual ≤ ACP and
   → 0 when VRE covers the target, capacity-revenue monotonicity of the retirement
   screen (call apply_economic_retirements directly on a crafted 3-unit fleet), and the
   ERCOT zero-capacity-revenue negative control. NOT @slow — this is the per-PR gate the
   testing audit found missing (its G2/G3/G4).
3. Wire the weekly forecast-invariants.yml artifacts to also commit their findings JSON
   to docs/handoffs/weekly-invariant-findings/ (append-only) so weekly results stop being
   ephemeral (testing-audit G9). Keep runtime budget unchanged.
Do NOT run the full battery in this session (that is P-1A) — smoke one rung per ladder
to prove the harness. Tests green; push via mcp__github__push_files.
```

### P-0B [SONNET] — Capacity-market design & auction-history intake

```
[SONNET] P-0B — Data intake: capacity-market demand curves, net-CONE, ELCC, auction history

Read CLAUDE.md, the data-intake skill, and docs/handoffs/
forecast-driver-capacity-revenue-audit-plan-2026-07.md §3–§4 (N1–N6). Fresh branch.

Intake, as new datatypes under data/raw/capacity-market/ with schema/dictionary entries
and a curation script each (schema-first; write_clean/read_clean seam; per-ISO registry
modules, no if-iso ladders):
1. Demand-curve parameters per ISO: PJM VRR points + net-CONE + IRM (current BRA planning
   parameters), NYISO ICAP demand curves, ISO-NE FCA/MRI curve parameters, MISO PRA
   reliability-based demand curve + seasonal CONE, CAISO CPM soft-offer cap + CPUC RA
   report prices. Record vintage + source URL per row.
2. Auction clearing-price history per ISO (PJM BRA by delivery year incl. 2025/26 and
   2026/27; NYISO spot monthly→annual; ISO-NE FCA; MISO PRA seasonal), delivery years
   ≤ 2026/27 only.
3. ELCC/accreditation curves: PJM ELCC class ratings, MISO wind/solar ELCC by
   penetration, NYISO/ISO-NE equivalents (N6) — capture the penetration axis, not just
   the current point.
Everything here is published market-design data (rule 13-admissible input) or published
outcomes (validation observables — mark them so in the dictionary: NEVER a fit target).
If a source is login-walled or the proxy blocks it, log the exact URL + error in
docs/handoffs/capacity-market-intake-<date>.md under "MANUAL DOWNLOADS NEEDED" and move
on — do not guess values. No LP solves. Tests: loader-resolvability + schema round-trip
with tmp-CLEAN_DIR. Push via mcp__github__push_files.
```

### P-0C [SONNET] — Forward-driver data files (AEO/ATB/uranium/carbon programs/IRA statute)

```
[SONNET] P-0C — Data intake: AEO2025 fuel paths, ATB cost trajectories, uranium, carbon
programs, post-OBBBA credit parameters

Read CLAUDE.md, the data-intake skill, and docs/handoffs/
forecast-driver-capacity-revenue-audit-plan-2026-07.md §4 (N7–N11, N15). Fresh branch.

1. EIA AEO2025: pull the Henry Hub, coal (by supply region if easy, national if not),
   and oil price series (reference + high/low supply side-cases) via the EIA API/table
   browser into data/raw/eia-aeo/ with a curation script. This resolves the standing
   "TODO: verify against AEO Table 13" at constants.py:914. Do NOT change
   HENRY_HUB_TRAJECTORIES values in this session — produce a diff report
   (hardcoded vs fetched, per year/path) in docs/handoffs/aeo-verification-<date>.md;
   the constants re-derivation is P-1D's job with rule-23 citation of this data change.
2. NREL ATB 2024 workbook (CSV via OEDI) into data/raw/nrel-atb/: capex/FOM by tech ×
   year × case — the calendar-year trajectories D4 needs.
3. EIA uranium marketing annual → $/MMBtu nuclear fuel series (N11).
4. RGGI + CARB auction results through latest (N10) — refresh anchors, note current
   program parameters (CCR/ECR triggers, floor).
5. IRS/statute parameters for §45U and the 45Y/48E tech-neutral successors as enacted
   (N15) — a small cited YAML/CSV under data/raw/policy/, feeding P-1C.
Same discipline as P-0B: schema-first, no value guessing, MANUAL-DOWNLOADS-NEEDED log
for anything blocked, no LP solves, push via mcp__github__push_files.
```

### P-1A [SONNET] — Run the Tier-1 driver battery ⛔

```
[SONNET] P-1A — Execute the Tier-1 driver ladders and commit the findings

Read CLAUDE.md and docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md
§2 Tier 1. Requires P-0A merged. Fresh branch.

Run scripts/run_driver_battery.py for all nine ladders (T1.1–T1.9) on ERCOT + PJM
(T1.6 on NEISO or CAISO), 2026–2030, legacy bins. Launch independent ladders as
concurrent background jobs with separate --out-dirs, ≤2 simultaneous (rule 12);
years within each invocation sequential. Commit
docs/handoffs/driver-battery-<date>.md + .json: per-test PASS/FAIL against the
pre-registered expectations, the elasticity magnitudes (report-only round), and for
every FAIL a one-paragraph mechanism hypothesis naming the responsible module —
findings only, NO model-code fixes, NO threshold widening (rules 1/11/14). File a
GitHub issue per directional FAIL. These are forecast probes: no backcast-dashboard
registration. Push via mcp__github__push_files.
```

### P-1B [OPUS] — CR-1: sloped capacity demand curve

```
[OPUS] P-1B — Implement reserve-margin-indexed capacity demand curves (CR-1)

Read CLAUDE.md, then docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md
§3 (THE SPEC for this session), then docs/handoffs/capacity-economics-plan-2026-07.md §0
scope guard (same guard applies: annual capacity-evolution layer only; never touch the
dispatch-layer floors). Requires P-0B merged. Fresh branch.

1. Extend MarketDesign (constants.py) with published demand-curve points + citation
   fields per ISO, loaded/validated from the P-0B capacity-market datatype. CAISO keeps
   the fixed proxy, re-cited to CPM/CPUC-RA (documented low-fidelity member).
2. capacity_revenue_per_mw_yr grows a curve mode: capacity_price =
   VRR_iso(accredited_firm_capacity_mw / requirement_mw) — reuse the exact requirement
   the floor/backstop already compute (one requirement, one basis, rule 19). Gate:
   ScenarioConfig.capacity_market_clearing, default OFF (byte-identical default paths —
   prove with a test). All three consumers (retirement, thermal entry, storage entry)
   flow through the same seam; no screen-specific curves.
3. Add capacity revenue (fixed or curve, labeled) to results/plant_financials.py.
4. Tests trivial-first (1-unit fleet, hand-computed curve points): price-at-requirement
   = net-CONE; zero-cross; cap; monotonicity; ERCOT returns 0 in both modes; default-off
   byte-identity; T2.1 arithmetic-identity test.
5. Update model-methodology-spec.md §5 + this plan's §3 status line. NO default flip in
   this session — that is gated on P-2A. Push via mcp__github__push_files.
```

### P-1C [SONNET] — IRA §45U + tech-neutral successors

```
[SONNET] P-1C — Add §45U nuclear PTC and 45Y/48E tech-neutral credit semantics

Read CLAUDE.md, src/market_sim/policy/ira.py, and docs/handoffs/
forecast-driver-capacity-revenue-audit-plan-2026-07.md §1 D5. Requires P-0C's statute
parameters. Fresh branch.

1. ira.py: add the §45U existing-nuclear PTC (credit as enacted incl. the gross-receipts
   phase-down and its expiry year) so the NUCLEAR retirement screen sees it as revenue —
   thread through the same attribute-revenue seam EAC/ZEC uses, taking
   max(45U, eac_price_nuclear, rps_shadow-if-eligible) so support is never
   double-counted (one mechanism per phenomenon, rule 19). New ScenarioConfig fields
   with statute citations (rules 5/24); policy_bundle offsets apply coherently.
2. Add 45Y/48E semantics for post-2025 vintages per the enacted phase-out schedule,
   replacing the hard binary cliff where the statute is a ramp — keep the current
   fields' behavior reproducible via the bundle system (no silent default change to
   existing scenarios; document any default that does move).
3. Tests: nuclear unit un-retires when 45U covers its FOM gap and retires after expiry;
   wind/solar entry economics continuous across the 45Y transition per statute; bundle
   offsets shift all cliffs together. Update docs/parameter-citations.md. Push via
   mcp__github__push_files.
```

### P-1D [SONNET] — Driver completeness batch

```
[SONNET] P-1D — Driver completeness: AEO-file wiring, coal/oil paths, uranium,
carbon_program_price_path, PJM RGGI option, DC tables

Read CLAUDE.md and docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md
§1 D2/D3 + §4. Requires P-0C merged. Fresh branch. Coordinate constants.py sections
with P-1B if concurrent (disjoint tables; rebase before push).

1. Re-derive HENRY_HUB_TRAJECTORIES from the P-0C AEO dataset (rule 23: cite the data
   change; the derive script reads data/raw/eia-aeo/, never a residual). Same for a new
   COAL_PRICE_TRAJECTORIES (replacing flat 1%/yr) and an oil path. Replace the
   last-YoY-ratio extrapolation beyond the AEO table (fuel.py:178) with
   hold-last-real-value flat — a naive compounding tail is a silent driver.
2. Nuclear fuel: replace the $0 placeholder with the EIA uranium-marketing-derived
   $/MMBtu series + AEO escalation (data-cited constant, ScenarioConfig-overridable).
3. Wire carbon_program_price_path (scenarios.py:122 — declared but dead): named
   projected program-price paths for RGGI/CARB as an alternative to the floor-band
   escalator, table in constants.py cited to program annual reports.
4. PJM RGGI: add the optional budget/membership entry (VA-era membership as published)
   so mass_cap_enabled works for PJM — default inert exactly as today.
5. DC tables: fill MISO/NEISO DATACENTER_ADDITIONS_MW from published ISO decompositions
   if P-0C/N12 found any; else leave 0 and add the explicit "no published source" note.
Tests per change (trajectory resolution, extrapolation behavior, PJM cap row builds,
byte-identity where defaults shouldn't move). Push via mcp__github__push_files.
```

### P-2A [OPUS] — CR-2: validate capacity prices against auction history ⛔

```
[OPUS] P-2A — Validate the capacity demand curves against published auction outcomes

Read CLAUDE.md and docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md
§3.3 + §2 T3.1. Requires P-1B + P-0B merged. Fresh branch.

Build scripts/validate_capacity_prices.py: for each capacity-market ISO and delivery
year ≤ 2025/26 with published data, evaluate the implemented curve at the PUBLISHED
reserve-margin/accreditation position (from P-0B planning parameters — not the model's
own fleet, this isolates the curve from fleet error) and compare with the published
clearing price. Then a second pass using the model's own hindcast-year accredited
positions (ERCOT excluded) where hindcasts exist. Commit
docs/handoffs/capacity-price-validation-<date>.md: per-ISO-year table (curve price vs
cleared price), regime-reproduction verdict (does PJM's 2024/25→2025/26 spike direction
reproduce?), residual discussion. HARD RULES: comparison only — no curve-parameter
adjustment, no multiplier (rules 1/13/23); H1-2026-delivery rows shown greyed,
excluded from verdicts. End with a recommendation memo: flip
capacity_market_clearing default on/off per ISO, with rationale. If recommended ON,
flip in a dedicated commit citing this report, and re-run the affected Tier-1 ladder
(T1.7) + tornado capacity entries. Push via mcp__github__push_files.
```

### P-2B [FABLE] — FPR / accreditation-basis adjudication memo

```
[FABLE] P-2B — Adjudicate the ICAP/UCAP/FPR accreditation-basis mismatch (#1532)

Read CLAUDE.md, docs/gap-register-2026-07.md (the #1532 addendum), docs/handoffs/
forecast-driver-capacity-revenue-audit-plan-2026-07.md §3.4.2, the P-2A validation
report, and the relevant code (capacity.py accreditation + requirement paths,
PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO). No code changes — memo session.

Write docs/handoffs/accreditation-basis-memo-<date>.md: (a) the three bases now in
play (published FPR ≈ marginal-ELCC-embedded; model (1−EFORd) supply UCAP; ICAP-basis
PRM with ratio correction) and where each enters requirement vs supply vs payment;
(b) the sign-flip risk #1513/#1532 flagged, quantified on the P-2A numbers;
(c) a single recommended basis for requirement, supply, and the CR-1 curve position,
with the migration path and which published parameter re-derivations it triggers;
(d) how CR-3.1 marginal-ELCC curves change the answer. End with the owner-decision
box (options, recommendation, what each option re-opens). Push via
mcp__github__push_files.
```

### P-2C [OPUS] — CR-3.1: marginal-ELCC accreditation curves

```
[OPUS] P-2C — Penetration-indexed ELCC curves for wind/solar (and storage reconcile)

Read CLAUDE.md, docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md
§3.4.1, the P-2B memo (follow its adopted basis), and the P-0B ELCC datatype. Fresh
branch.

Replace the flat RENEWABLE_CAPACITY_CREDIT wind 0.16 / solar 0.18 with per-ISO
penetration-indexed piecewise-linear ELCC curves digitized from the published ISO
studies (P-0B/N6), falling back to the flat constant where no study is published
(cited, neutral fallback — rule 25 spirit). Penetration = the model's own installed
share (regenerates forward, responds to build — rule 13). Reconcile with the existing
storage duration-ELCC + saturation + dilution stack so storage isn't double-derated
(one mechanism per phenomenon — enumerate what already derates storage before adding
anything, rule 19). Consumers: accredited_firm_capacity_mw, the floor, the backstop,
and the CR-1 curve position move together. Tests: curve interpolation vs hand values;
credit falls as penetration rises; T1.9 ladder re-run; frozen-penetration
byte-compat mode for the hindcast baseline comparison. Then re-run the ERCOT+PJM
capacity hindcasts (before/after diagnostic, registered on the forecast-validation
dashboard like the Stage-2 precedent). Push via mcp__github__push_files.
```

### P-3A [SONNET] — First full-horizon runs ⛔

```
[SONNET] P-3A — First full 2026–2050 forecast solves, all six ISOs, invariants scored

Read CLAUDE.md and docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md
§2 (testing-audit G1: the full horizon has never been run). Requires Wave 1 merged;
run with capacity_market_clearing per the P-2A decision (or both A/B if undecided).

For each ISO: reference forecast config, 2026–2050, CAMPD bins where that is the ISO
default, years sequential within each invocation, ≤2 ISO invocations concurrent
(rule 12 — per-plant multi-zone cap), separate --out-dirs, background jobs. Run
scripts/check_forecast_invariants.py (I1–I14) on every completed run. Commit
docs/handoffs/full-horizon-findings-<date>.md: wall time + peak RAM per ISO-year
(feasibility data for making this a release gate), per-invariant PASS/FAIL per ISO
with offending years, F1/F2 status at horizon (does de-firming compound to 2050?),
capacity/price/CO2 trajectory summary tables, and a ranked issue list. Findings only —
no fixes, no threshold changes. Extend the golden fixture to one deeper checkpoint
(e.g. 2040) if runtime allows. Forecast probes: no backcast-dashboard registration.
Push via mcp__github__push_files.
```

### P-3B [SONNET] — Tier-2 equilibrium battery

```
[SONNET] P-3B — Capacity-market equilibrium tests (T2.1–T2.5)

Read CLAUDE.md and docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md
§2 Tier 2. Requires P-1B (+P-2A decision) and P-3A merged.

Extend scripts/run_driver_battery.py with the Tier-2 suite: T2.1 price-to-curve
identity on the P-3A PJM run; T2.2 long-run price-vs-net-CONE oscillation statistics
(PJM/NYISO/MISO 2026–2050); T2.3 hysteresis (reuse I5/I13); T2.4 +10 GW exogenous
overbuild probe (PJM) — price collapses along the curve, entry stops, retirements
resume; T2.5 the same overbuild on ERCOT — adequacy signal expresses through
ORDC/AS revenue instead. Commit docs/handoffs/equilibrium-battery-<date>.md with
pre-registered PASS/FAIL + mechanism hypotheses for failures. Findings only.
Push via mcp__github__push_files.
```

### P-3C [FABLE] — Cross-model corridor + updated fitness verdict

```
[FABLE] P-3C — Cross-model benchmark corridor and the updated forecast-fitness verdict

Read CLAUDE.md, docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md,
the P-1A/P-3A/P-3B findings, docs/forecasting-entry-exit-assessment.md (the verdict
you are updating), and the latest hindcast reports. WebSearch/WebFetch allowed.

1. T3.3: compare the P-3A frozen-config 2026–2035 trajectories against EIA AEO
   (latest), NREL Standard Scenarios mid case, ERCOT CDR, and each ISO's planning
   outlook: capacity by tech, retirements, energy mix, reserve margin. One-paragraph
   ours-vs-theirs explanation per material divergence (>15%) — divergence is not
   failure; unexplained divergence is.
2. T3.2: refresh the screen-revenue vs SOM/PNM table for every ISO with a published
   SOM (extends the ERCOT-only capacity-economics §5 audit).
3. Rewrite docs/forecasting-entry-exit-assessment.md's verdict table for the
   post-CR-1/CR-3 model: which entry/exit calls are now defensible, which remain
   unfit, and what the remaining blockers are (tie to gap-register IDs). This is the
   deliverable the whole program is graded on — be adversarial, not celebratory.
Push via mcp__github__push_files.
```

### P-3D [OPUS] — Hindcast re-score + extend coverage

```
[OPUS] P-3D — Re-score ERCOT/PJM capacity hindcasts post-CR; extend to MISO + NYISO

Read CLAUDE.md, docs/handoffs/forecast-validation-program-2026-07.md §1 (harness +
§6 baseline misses), and docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md
§2 T3.4. Requires CR-1 (+CR-3.1 if landed).

1. Re-run the ERCOT + PJM 2021–2025 realized-fuel hindcasts at HEAD with the new
   capacity-revenue/ELCC stack (concurrent background jobs, separate out-dirs) and
   re-score with score_capacity_hindcast.py. Register before/after on the
   forecast-validation dashboard. The question: does PJM's thermal-retirement −63%
   and over-build improve when the capacity price can respond to the fleet?
   Attribute per screen; findings only, no tuning.
2. Build capacity_actuals CSVs + hindcast configs for MISO and NYISO (next two ISOs
   by data readiness); run + score their 2021–2025 realized hindcasts.
3. Update docs/handoffs/forecast-validation-program-2026-07.md §6 status.
Push via mcp__github__push_files.
```

---

## 7. What this plan does NOT do

- It does not tune anything to a residual — every FAIL routes to a root-cause
  issue (rules 1/11/14).
- It does not touch the AS co-opt flagship (G-20/G-22/W22) or the FOM flip —
  those stay in their lanes; this plan's T3.2 keeps their gap measured.
- It does not solve or score 2022/H1-2026 anywhere (rule 22 unchanged;
  NEISO's marker is not consumed by any session here).
- It does not build full auction supply-curve clearing, CP/PAI penalties,
  Y-3 forward lag, or locational curves in the first pass (§3.2 out-of-scope
  list; revisit on CR-2 evidence).

*Produced 2026-07-11. Code anchors verified against `origin/main` at HEAD
(keepers as of `2026-07-11-nyiso-61-downstate-import` vintage).*
