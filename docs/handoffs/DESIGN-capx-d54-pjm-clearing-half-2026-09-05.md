# DESIGN — capx D54: the PJM clearing half — clear the fleet's net-ACR sell-offer stack against the published VRR curve, and let the UNCLEARED set be the retirement screen's capacity leg (D45 §2.3 item 3; the last structural piece of the D6 / D28 chain)

**Lane:** capx D54 — director r#35, docs-only (`docs/handoffs/capx-director-ledger-2026-08.md`
§0af.2: "design + pre-declaration only; code and solve GATED on D48 landing"). Branch
`claude/capx-d54-pjm-clearing-design`, fresh off `origin/main` (`d9f034f`). **No code, no
solve, no `ScenarioConfig` field, no matrix row** (rule 28 is the build lane's duty and is
listed in §7). D48 HAS landed (`FINDING-capx-d48-2026-09-04.md`, PR #4707 + Phase 1): its
result does NOT change this design — it strengthens the case for it (§0, §4.6) — and it
adds one arm to the A/B plan (§7.6). The companion pre-declaration is
`PREDECL-capx-d54-pjm-clearing-half-2026-09-05.md`; its zero-solve instrument and
outputs are committed under `docs/handoffs/d54/`.

**DATA PROFILE: code.** Everything below is read from committed artifacts (the D45-R and
D48 T1-H bundles' `evolution_<year>.json` ledgers, the D48 position instrument, the D45
published-positions instrument, the committed PJM auction CSVs) and from PJM's own
published rules, fetched and hashed this session (§8).

---

## 0. The design in one paragraph

PJM's Reliability Pricing Model does not evaluate the VRR curve at the installed fleet: every
existing Generation Capacity Resource must submit a **sell offer**, each offer is **capped at
the unit's net Avoidable Cost Rate** (gross ACR minus its energy-and-ancillary net revenue,
converted to UCAP), the offers form a **supply curve**, and the auction clears where that
supply curve meets the VRR curve — price at the intersection, **cleared units paid the
clearing price, uncleared units paid nothing**. The model today (`capacity_market_clearing`,
K/K for PJM) evaluates the same published curve at the CENSUS position and pays every unit
the resulting price, which D45 §2.2 / D48 §2 measured as 4–11 points past the curve's zero-
cross in 2022–2024 — $0 for every unit, where the auction paid $10.6–18.3/kW-yr at a
cleared position 1.05. The model already carries every operand the real mechanism needs:
the retirement screen's **going-forward cost** is the unit's gross ACR, its **attainable
E&AS net revenue** is the E&AS offset, and D48's `accredited_firm_capacity_mw` seam is the
UCAP conversion. So the design is: **per unit, offer = max(0, going-forward cost − E&AS net
revenue) ÷ accredited MW; stack every accredited MW of the entering fleet (screened thermal
at its offer, everything else — VRE, hydro, storage, firm imports, Demand Resources, and
every screen-exempt unit — as a price taker at $0); clear the stack against the delivery
year's published VRR curve on the D48 basis; the cleared set earns the clearing price on its
accredited MW, the uncleared set earns $0; and the retirement screen's capacity leg is that
per-unit settlement instead of one census price broadcast to all.** With that construction
the screen's failing set IS the auction's uncleared set (§3.5 proves it), the census
evaluation is recovered exactly whenever every offer is $0 or the market is short (§3.6
I1), and there is **no free parameter**: every number is either a published market-design
parameter already in the registry or an operand the screen already computes. The zero-solve
instrument (§8, `docs/handoffs/d54/`) run on the committed ledgers puts the design's cleared
position within **0.7 / 1.0 / 2.6 points** of the published cleared position in 2022/23,
2023/24, 2024/25 — and its clearing price at **1.7× / 2.4× / 5.5×** the published price,
because the model's offer stack is too expensive: the gas-CT, gas-steam and oil fleets carry
exactly zero E&AS margin in the hindcast prices (D45 §1 (i)), so ~65 GW of offers sit above
the published price where the auction record shows ~9–20 GW uncleared. That is the design
working as a **measurement instrument** — it converts the "$0 where the model sat" defect
into a statement about the E&AS operand — and it is pre-declared as such: a build that lands
on the published price without an operand change is refused (PREDECL §4).

## 1. The object and the record it closes

| record | what it established | what it left |
|---|---|---|
| D28 §4, §6.5 (`FINDING-capx-d28-longposition-capacity-revenue-2026-09-01.md`) | "evaluate the curve at the fleet census" is a category error even with perfect accreditation: reality's position is curve-endogenous (de-list bids, sell offers, the marginal offer), the model's is curve-exogenous; the PJM instance is a position defect in the hindcast, self-resolving from 2028/29 by the ER26-1556 floor | the cross-ISO clearing half as a chartered mechanism question, identified from each ISO's published offered-vs-cleared quantities |
| D31 §2 (`FINDING-capx-d31-miso-caprev-repair-2026-09-02.md`) | MISO's worked example: the census counted +17 % more internal supply than the PRA's own offered Generation; the vertical-era PRA cleared EXACTLY the PRMR by construction, so "the right census comparison for a model position is the OFFERED position" | the accounting ratio (0.8546) reconciles MISO's census to its offered stack — a per-ISO number that transfers nothing (rule 25) |
| D45 §2.1–§2.3, §3(a), §4.0–§4.1, §6, §9 | PJM's $0 is a basis artifact on top of a clearing-half artifact; on the auctions' own UCAP basis the entering screens sit at/near the cleared position and the published curve at the published cleared position pays $15–21/kW-yr; the zero-solve re-screen at $20.86/kW-yr passes 13.0 of 18.1 GW of the 2022 coal decisions; the L1/L4 pair brackets the truth from both sides ($0 over-retires by 6.7 GW, flat $77.43 fails nothing) | §2.3 item 3, the clearing half: "clear the VRR curve against the fleet's net-ACR offer stack rather than evaluate it at the census … the model already carries every ingredient" — successor per-ISO lane |
| D48 §2, §3.3, §5 item 1, §8 (`FINDING-capx-d48-2026-09-04.md`) | the accreditation devintage + DR-as-supply land the accounting on the auction's own basis (requirement rows to the MW), leave the census position 7–11 points past the zero-cross ($0 in both arms), and move FC-3 the wrong way through the admission cap — "a faithful basis over an unfaithful price"; recommendation: do not arm alone, route WITH the clearing half, which §3.3(d) makes the PRECONDITION for arming the devintage | this lane |

The charter (director r#35): "clear the VRR curve against the fleet's net-ACR offer stack
(Manual 18 §6 / MSOC) instead of evaluating it at the census; design + pre-declaration
only". One citation correction, stated because a successor will look for it: in Manual 18
Revision 62 (the current revision, fetched and hashed in §8), **Section 6 is "Capacity
Transfer Rights"**; the sell-offer-cap rules are **§5.4.1 / §5.4.4 / §5.4.7 / §5.4.8.4(B)**
and they defer to **Tariff Attachment DD §6.4 (sell offer caps), §6.6 (must-offer), §6.7
(ACR data), §6.8 (ACR definition and the E&AS offset)**. D45's "Manual 18 §6" is the same
material under its Attachment DD number.

**Lever-queue check (rule 28 (a)).** The PJM backcast lever queue is EMPTY and closed
(`docs/mechanism-testing-matrix.md` §5.3, pjm-153); this is a FORECAST-lane mechanism and
enters through the capx director's queue, where it is the routed successor of D45 §2.3 item
3 and D48 §5 item 1. The PJM shard's `capacity_market_clearing` cell reads K/K (the curve
is the published design and stays ON); this design changes the QUANTITY the curve is
evaluated at, not the curve. No cell adjudicated R/I/G is re-tested.

## 2. PJM's own mechanism, as published (the rules the design mirrors)

Source: PJM Manual 18 *PJM Capacity Market*, Revision 62, effective 2025-12-17
(`https://www.pjm.com/-/media/DotCom/documents/manuals/m18.ashx`, sha256
`f188c587d5e00112e5dfa1ab84a793cb335f72bf82b23caa31c488fe8e929bfa`, 289 pp.; §8), and the
five BRA reports D45 §8 hashed, re-fetched here with identical hashes.

1. **Must-offer.** Every Existing Generation Capacity Resource in a seller's portfolio
   must be offered into the BRA for the Delivery Year unless it holds an exception (Manual
   18 §5.4.1 / §5.7.1; Att DD §6.6). Exceptions are enumerated: physical incapability of
   meeting Capacity Performance, a firm external sale, or a request to **remove Capacity
   Resource status** (§5.4.7 — the deactivation path: once removed, the unit "will be
   removed from the Capacity Resource model and no longer eligible to offer in RPM
   auctions"; a request is refused while the unit holds a commitment). Demand Resources
   are not subject to the CP must-offer (§5.4.1) and **no offer caps apply to DR** (§5.4.4).
2. **The Market Seller Offer Cap.** "A Capacity Market Seller submitting a sell offer for
   an existing Generation Capacity Resource … greater than $0/MW-Day must seek a
   unit-specific exception request … by submitting Avoidable Cost Rate data to IMM and
   PJM 120 days prior to the RPM Auction, or may, at its election, utilize an offer cap
   based on the default gross Avoidable Cost Rate of the applicable resource type"
   (§5.4.1, effective 2021-09-02 per the Revision 52 log). The cap is the **net ACR**: the
   avoidable cost "assuming the unit would otherwise retire" (§5.4.4, categories per Att DD
   §6.8) **minus Projected PJM Market Revenues** — "all actual unit-specific revenues from
   PJM energy markets, ancillary services, and unit-specific bilateral contracts … net of
   energy and ancillary services market offers … the rolling simple average of such net
   revenues from the three most recent whole calendar years" (§5.4.4, Att DD §6.8(d)).
   Default gross ACR (2022/23 $/MW-day, nameplate, through DY 2025/26): coal 80, CC 56, CT
   50, steam oil & gas n/a, nuclear single/multi 697/445 (§5.4.8.4(B); committed at
   `data/raw/capacity-market/avoidable-cost-rate/pjm/pjm.csv`).
3. **UCAP conversion.** "Through the 2024/2025 Delivery Year the net ACR is converted to
   UCAP MW terms based on the unit-specific EFORd … Beginning with the 2025/2026 Delivery
   Year … based on the resource-specific Accredited UCAP Factor" (§5.4.8.4(B)) — exactly the
   D48 vintage axis.
4. **Mitigation applies to everyone.** "The RTO as a whole failed the Market Structure Test
   (the Three-Pivotal Supplier Test), resulting in the application of market power
   mitigation to all Existing Generation Capacity Resources … utilizing the lesser of the
   supplier's approved Market Seller Offer Cap … or the supplier's submitted offer price"
   (2022/2023 BRA Report p. 4; the same sentence in every report of the window). So in the
   hindcast window the effective offer of every existing unit is **≤ its net ACR**, which
   is what licenses the design's use of the cap AS the offer.
5. **Clearing and settlement.** The BRA clears the sell-offer supply curve against the VRR
   curve; cleared MW receive the Resource Clearing Price; "unoffered" and uncleared MW
   receive nothing and unoffered existing MW are excluded from the incremental auctions
   (§5.7.1). The record of what did not clear is Table 6 (offered / cleared / uncleared
   UCAP) of every BRA report and Table 7 of the 2024/2025 report (offered / cleared **by
   resource type**, 2021/22–2024/25) — the design's validation observables (§5).
6. **What the model will not represent** (stated, with the published magnitude): the
   2021/2022 expanded MOPR floors that left 10.6 GW UCAP of nuclear uncleared (Table 7;
   the December 2019 MOPR order applied to state-supported units, superseded from
   2023/24 by Att DD §5.14(h-2)); per-LDA clearing (the model's PJM curve is the RTO curve
   — locational is `capacity_deliverability_limits`, its own gated mechanism); the
   incremental auctions; and the FRR carve-out (§4.6).

## 3. THE MECHANISM — stated so a successor builds it without design choices

### 3.1 Operands (every one already exists; none is new)

| symbol | quantity | where it already is | basis |
|---|---|---|---|
| `GFC_g` | going-forward cost, $/yr | `apply_economic_retirements`: `fixed_om_<fuel> × retirement_fom_multiplier_<fuel> × pmax_mw × 1000` (`retirements.py`, the `going_forward_cost` the screen's bar is) | the unit's gross ACR proxy — the bar the screen already identifies (rule 23); the coal 1.3× stays because the offer is the seller's indifference price against **that** bar, and one bar decides both offer and exit (rule 19) |
| `EAS_g` | E&AS net revenue, $/yr | the same function's `net_revenue` **before** the capacity leg is added — `energy_margin + reserve_uplift + attribute_revenue (+ §45U) + as_annual_credit`; in the committed ledgers exactly `net_revenue_usd − capacity_revenue_usd` (`capacity_revenue_usd` is 0 in every 2022–2024 row) | the screen's own prior-year attainable pro-forma (spec §5.2) — the Potomac-SOM construction the MSOC offset is also built from; **one year, not PJM's three-year average** (§4.8) |
| `A_g` | accredited MW | `_thermal_firm_mw(g, iso, config, year)` = `pmax × thermal_accreditation_fraction(fuel, eford, iso, config, year)` — the D48 seam (UCAP `1 − EFORd` per unit through DY 2024/25, ELCC class from 2025/26 when `pjm_accreditation_design_vintage` is on; ELCC class in every year when it is off) | the auction's own UCAP conversion (§2 item 3) |
| `Q_0` | the price-taking block, MW | every term of `accredited_firm_capacity_mw(...)` that is not a screened thermal unit: wind/solar pools at their ELCC credit, hydro, storage ELCC, the firm-import credit, DR under `pjm_demand_response_supply`, plus every screen-exempt unit's `A_g` (§3.2) | the same ledger the census position sums — so `Q_0 + Σ_g A_g = accredited_firm_capacity_mw` exactly (invariant I1) |
| `R` | requirement, MW | `resolve_adequacy_requirement_mw(config, iso, peak, year)` — D48's published pre-CIFP FPR × peak before 2025/26, post-CIFP FPR × peak from it (or HEAD's composite when D48 is off) | the position's own denominator (rule 19: one requirement, one basis) |
| `VRR_y(x)` | the delivery year's curve, $/kW-yr at ratio `x` | `resolve_demand_curve_vintage("PJM", year)` → `evaluate_demand_curve(vintage.demand_curve, x) × vintage.net_cone_curve_per_kw_yr`; delivery year `resolve_delivery_year("PJM", year)` = `"{year}/{year+1}"` | the published curve the model already prices (the 2021/22–2028/29 vintages in `config/capacity_market.py`) |

### 3.2 The sell offer and the stack

For every thermal unit `g` the screen evaluates (it has a `_THERMAL_FOM` entry, dispatch
rows, and is not in `exempt_unit_ids`):

```
offer_g  [$/MW-day, accredited]  =  max(0, GFC_g − EAS_g) / (A_g × 365)
```

Stack membership, by class of resource — the rule is *"every accredited MW the ledger counts
enters the stack exactly once; a MW whose exit the screen decides enters at its net ACR;
every other MW enters as a price taker at $0"*:

| resource | enters at | why |
|---|---|---|
| screened thermal (coal, gas_cc, gas_ct, gas_st, oil, nuclear, biomass, gas_cc_ccs) | `offer_g` on `A_g` | the must-offer + MSOC (§2 items 1–2, 4) |
| a screened unit whose `EAS_g ≥ GFC_g` | `offer_g = 0` | the cap formula — a unit covering its avoidable cost offers as a price taker (Manual 18: a seller needs ACR data only "to submit a sell offer greater than zero") |
| screen-EXEMPT units: plants with a pending owner-filed date (`dated_plant_unit_ids`, rule 19 D42/D44), this-year CCS retrofits, and — if D53 lands — sector-gated units | price taker at $0 on `A_g` | their exit is decided elsewhere, so no offer can change their decision; the screen computes no `EAS_g` for them, and inventing one would be a second operand. Scope: a dated unit still in the fleet for the delivery year DOES sit in the stack (it must offer for delivery years before its filed exit — §2 item 1); a unit dated out by step 0/1 is not in the fleet and is absent. (§4.2) |
| wind / solar pools, hydro, storage, firm imports (`ADEQUACY_EXTERNAL_TIE_FIRM_MW`), Demand Resources (offered DR under D48, else absent because netted) | price taker at $0 on their ledger credit | no cap applies to DR (§2 item 1); VRE/hydro/storage carry no going-forward bar in the model; imports are the cleared external quantity by construction |
| economic new entry, planned additions | **not in the stack** (§4.4) | the entry screen is already a price-taking margin test at the clearing price |

Nothing else enters, nothing is withheld: no offer floor, no offer adder, no bid-shading
parameter. A unit's offer is a deterministic function of the screen's two operands and the
D48 accreditation.

### 3.3 The demand side

The VRR curve is evaluated in ratio space exactly as today: `D(Q) = VRR_y(Q / R) × 1000 / 365`
in $/MW-day, flat-extrapolated at the cap below the first published point and at the last
published point above (the zero-cross for 2021/22–2027/28; the ER26-1556 floor for
2028/29+, `evaluate_demand_curve`). The ratio convention is the one D28/D45/D48 already use:
an RTO-wide stack against an RTO-wide requirement, read as the RPM ratio (FRR entities
scale out proportionally — §4.6 states the size of that assumption and its published
refinement). `curve_convention_position` (NEISO's raw/net DR re-expression) is inert for
PJM and stays so.

### 3.4 The clearing rule (exact, deterministic)

Sort offers ascending (`offer_g`, then `unit_id`) — the price-taking block `Q_0` is the
first step at $0. Walk the stack; with `q` the cumulative cleared MW before unit `g`:

1. **If `D(Q_0) ≤ 0`** (the price-taking block alone reaches the zero-cross): price 0,
   cleared quantity `Q_0`, cleared set = the price takers only, every screened unit with
   `offer_g > 0` is uncleared. (A screened unit with `offer_g = 0` is cleared — it is
   inside `Q_0`'s $0 step by construction; ties at $0 are all cleared, which is also what
   the auction does with $0 offers when the curve is at $0.)
2. **If `D(q) < offer_g`**: the curve crosses the supply curve on the vertical rise between
   the previous offer and `offer_g` — **price = `D(q)`** (the curve sets the price), cleared
   quantity `q`, `g` and everything above it uncleared.
3. **If `D(q + A_g) ≥ offer_g`**: `g` clears in full; continue.
4. **Otherwise** the curve crosses inside `g`'s step: **price = `offer_g`** (the marginal
   offer sets the price), cleared quantity = the `Q ∈ (q, q + A_g]` with `D(Q) = offer_g`
   (bisection on a monotone segment). **The marginal unit is treated as CLEARED in full for
   the screen** — at `price = offer_g` it is exactly indifferent (`EAS_g + price × 365 × A_g
   = GFC_g`), the auction itself clears its MW pro rata and pays the price on the cleared
   MW, and a whole-unit convention is the screen's grain (one-unit granularity, stated,
   never a parameter).
5. **If the walk exhausts the stack** (every offer below the curve — the SHORT market): price
   = `D(Σ)` at the full accredited quantity, everything cleared. This is the 2025 case and
   every forward-year case where the curve sits above every offer: **the design reduces to
   the census evaluation exactly** (I1).

The price is bounded in `[0, cap]` by the curve; it is monotone non-decreasing in every
offer and non-increasing in `Q_0` and `R`… (I3/I4). Complexity is one sort per screen year;
no iteration, no LP (rule 10 `[R-ONE-PASS]` untouched).

### 3.5 Settlement into the screens — and the identity it creates

- **Retirement screen (step 3).** `capacity_revenue_usd_g = price × 365 × A_g` for a cleared
  unit, `0` for an uncleared unit. Nothing else in `apply_economic_retirements` changes: the
  bar, the E&AS operand, the pipeline, the admission cap, the execution lag, the floor.
- **Identity (the design's structural statement):** a screened unit passes the bar iff
  `EAS_g + capacity_revenue_usd_g ≥ GFC_g`. For a cleared unit `price ≥ offer_g`, i.e.
  `price × 365 × A_g ≥ GFC_g − EAS_g` — it PASSES. For an uncleared unit `offer_g > price
  ≥ 0` and it is paid $0, so `EAS_g < GFC_g` — it FAILS. Hence **the failing set of the
  screen is exactly the uncleared set of the auction** (up to the whole-unit convention of
  the marginal unit), and the decision cohort the admission cap sizes is the set of units
  the market would not buy. That is the mechanism D45 §2.3 item 3 asked for: the screen no
  longer decides "who fails at one price"; it decides "who the market did not clear".
- **Thermal new entry and storage entry (steps 5, §5.3 / §5.5)** see the clearing `price`
  through the same seam they read today (`capacity_price_per_firm_mw_yr` → the price the
  clearing returned), as price takers (§4.4). The reserve-margin backstop and the floor
  read positions, not prices, and are untouched.
- **Ledger** (`evolution_<year>.json`, additive, decision-neutral): `capacity_clearing =
  {price_usd_per_mw_day, cleared_mw, cleared_position, price_takers_mw, offered_mw,
  uncleared_mw_by_fuel, n_uncleared, marginal_unit, how}` plus a per-row
  `capacity_cleared: bool` and `capacity_offer_usd_per_mw_day` on every `pipeline_events`
  row — so the next lane reads the stack off the ledger instead of replaying the solve
  (the D45/D48 observability discipline; nothing reads these back).

### 3.6 Invariants the build asserts (tests, in `tests/unit/model/test_capacity.py` beside `TestPjmAccreditationDesignVintage`)

- **I1 — census recovery.** With every `offer_g = 0` (all units pass), or whenever the
  curve sits above the highest offer, the clearing returns `price = VRR_y(accredited /
  R)` and `cleared = accredited_firm_capacity_mw` — byte-identical to today's census
  evaluation. Also the definition of the unarmed path: gate off ⇒ the seam returns the
  census price for every unit, as it does today.
- **I2 — the identity.** In every screen year, the set of screened units failing the bar
  equals the uncleared set (marginal unit excepted).
- **I3 — bounds.** `0 ≤ price ≤ VRR_y(first point)`; `Q_0 ≤ cleared ≤ Q_0 + Σ A_g`.
- **I4 — monotonicity.** Raising any single offer never lowers the price or raises the
  cleared quantity; raising `R` never lowers the price.
- **I5 — known answer.** On the committed D45-R and D48 ledgers the build's clearing
  function reproduces the pre-declaration instrument's price and cleared quantity per year
  to ±$1/MW-day and ±0.1 pt (PREDECL §2 tables, `docs/handoffs/d54/*.json`) — before any
  solve (the D48 Phase-0 discipline).
- **I6 — other ISOs byte-identical**; PJM unarmed byte-identical; the bare `pjm-t1h` key
  unmoved.

### 3.7 DOF ledger — zero

| number | source |
|---|---|
| `GFC_g` | the screen's own bar (`fixed_om_*`, `retirement_fom_multiplier_*`, NREL ATB / EIA S&L, already ledgered) |
| `EAS_g` | the screen's own prior-year pro-forma (prices, `mc`, availability, reserve signal — the solve's outputs) |
| `A_g`, `R`, `Q_0` | D48's seam and registries (published FPRs, ELCC class ratings, EFORd, DR series, tie credit) |
| `VRR_y` | the published vintage curves (planning-parameter workbooks, ER26-1556) |
| the clearing rule | the auction's own (price at the intersection, uncleared paid nothing) |
| whole-unit marginal convention | a grain statement, not a value |

No offer adder, no floor, no shading factor, no E&AS haircut, no per-fuel cap. The published
default gross ACR table (§2 item 2) is **not** used as a cap or a floor on the offer — it is
an election a seller may make instead of unit-specific data, and the model's unit-specific
bar is the more faithful operand; the table is cited as the external check on the bar's
LEVEL (coal 80 vs the model's 160 $/MW-day nameplate in 2022/23 $ — §6 item 5).

## 4. Interactions — decided and cited

### 4.1 The exit-rate cap (D45 §2.3 item 4; the D32/D42 object) — the pipeline's ADMISSION cap

Two different objects carry the name; both are stated. (i) **The admission cap** is the
reliability floor called at the cap horizon inside `_apply_pipeline_retirements`
(component 2; `_admission_cap_horizon`, D42's dated-exit netting, D48 §3.3): it retains
new candidates cheapest-firm-first until the scheduled post-pipeline firm clears the
requirement, so the decision cohort is at most the firm-MW **budget** `accredited(cap
fleet) − R(cap year)`. D45 §1 (i) called this "the pipeline's exit-rate cap" and D48 §3.3
measured that it — not the price — decides the composition today: 88.6 GW fails at $0 and
the cap admits 11.4–12.8 GW of it, coal first. (ii) **`exit_rate_limits`** (GATED
default-off, D-8) is the throughput cap on EXECUTION and is untouched by this design.

**How the uncleared set relates to the admission floor.** The design changes what the cap
SEES, not the cap: its candidate list becomes the uncleared set (§3.5), and every unit
above the cleared quantity fails whatever the cap does. On the committed 2022 ledgers that
list shrinks from 88.6 GW nameplate to **16.1 GW** on the D48 basis (coal 4.5, gas_cc 2.2,
gas_st 9.5) or **17.5 GW** on HEAD's basis (PREDECL §2), against a budget the D48 arm
realised at ~11.8 GW firm — so the cap still trims, but its role falls from selecting 13 %
of a 89 GW pool to trimming ~25 % of a 16 GW one, and it can no longer manufacture a
class ordering out of a $0-priced pool (D45 §2.3 item 4). The class ordering that remains is
the cap's own worst-first depth + cheapest-firm retention over the uncleared set: the
zero-E&AS coal (depth at the full $58.5 bar) is admitted first, the zero-E&AS gas steam
next (depth $35), gas_cc last — and the floor's retention buys back gas_cc ($31.6/firm-kW-
yr) before gas_st ($37.6) before coal ($63.6). Expected composition: PREDECL §3. Rule 19:
no second cap is added; the admission cap stays the one adequacy verb on the decision, and
its binding remains measurable through `entry_capped` rows.

### 4.2 The dates channel (rule 19: a dated unit does not offer)

A plant with a pending owner-filed date is exempt from the economic screen (D42/D44, the
`dated_plant_unit_ids` exemption). In the auction it must still offer for every delivery
year before its filed exit and stops offering once its removal / deactivation is effective
(§2 item 1, Manual 18 §5.4.7). The design's reading of "does not offer" is therefore **"does
not submit a price-forming offer"**: a dated unit still in the fleet for the delivery year
is a price taker at $0 on its `A_g` (its exit is the filed date's, so no offer can change it,
and the screen computes no `EAS_g` for it — a non-zero offer would need a second operand);
a unit whose date precedes the delivery year has already left through step 0/1 and is
absent from the stack. Consequence stated: price-taking dated MW biases the cleared
quantity UP and the price DOWN relative to letting them offer their net ACR; on the 2022
ledgers the in-window dated coal (~10.4 GW nameplate, D45 §4.0) would have offered at the
coal median (~$9/MW-day) and cleared anyway at the design's $83 price, so the bias is
second-order in the window and is reported by the ledger's `price_takers_mw`.

### 4.3 The reliability floor — what it still does when the market clears

Two verbs, one requirement (spec §5.2): the ADMISSION verb (§4.1) and the EXECUTION verb
(realized-year retention, component 5). The clearing changes neither's test
(`accredited ≥ R`); it changes the pool they act on. What the floor still does, explicitly:
(a) at admission it caps the uncleared set to the firm budget — the model's analogue of
PJM's deactivation reliability review / RMR retention (a unit that gives notice may be held
if the RTEP finds a reliability need; OATT Part V), which the real market applies exactly to
units that did NOT clear or did not offer; (b) at execution it retains due exits when the
realized year is short — the modelling-safety valve. Both stay measurable
(`floor_retained`, `entry_capped`, `floor_retention_log`). Design statement for the build's
finding: under a cleared market, floor binding above the D48 arm's level is a signal that the
uncleared set is too large — i.e. an E&AS-operand finding (§6 item 1), never a reason to
touch the floor. `market_design_retirement_floor` (energy-only skip) is irrelevant to PJM.

### 4.4 The entry side — new entry does not offer into the same stack

In the BRA, planned resources offer (capped at their net CONE-class cost) and clear when the
price reaches their offer; the model's entry screen (§5.3) tests `expected revenue (energy
+ capacity price × accreditation + AS) ≥ LCOE` — that is the same condition ("price ≥
offer") evaluated as a price taker at the clearing price. Adding entry offers to the stack
would decide entry twice (rule 19) and would need a per-candidate offer the screen does not
have. Decision: **entry, planned additions and storage entry stay OUT of the stack and read
the clearing price** through the existing seam. Stated limit: new entry cannot SET the
model's price (in the real auction it occasionally does, in the short LDAs); first-order
magnitude in the window is nil — an entry offer at net CONE sits above every existing offer
except zero-E&AS coal/nuclear, so it clears only when the curve is at net CONE, which is
exactly when the entry screen builds. Forward, in a short year the design and the census
evaluation coincide (§3.4 rule 5), so the entry side is unchanged there by construction.

### 4.5 The 2028/29+ price floor (D28 §4; ER26-1556)

From delivery year 2028/29 the VRR curve is collared at 175.00 / 325.00 $/MW-day UCAP and
never reaches zero (`_PJM_VRR_CURVE_2028_2029`), so `D(Q) ≥ 175` everywhere long. Under the
design every unit with `offer_g ≤ 175` clears whatever the position; only offers ABOVE the
floor can be uncleared. At the screen's own bars on the ELCC-class basis a **zero-E&AS**
unit offers: coal 58.5/0.83 → **193** $/MW-day (above the floor), nuclear 130/0.95 → **375**
(above), gas_st 35/0.73 → 131, gas_cc 30/0.74 → 111, gas_ct 21/0.60 → 96, oil 25/0.91 → 75
(all below). So forward the clearing half is INERT for gas and oil (they always clear at ≥
the floor and are paid it — D28's "$0-at-long ceases to exist" holds for them) and LIVE
only for coal with E&AS below `58.5 − 63.9 × 0.83 ≈ $5.5/kW-yr` and nuclear with E&AS
below `130 − 63.9 × 0.95 ≈ $69/kW-yr` — which is the published design's own consequence (a
unit whose net ACR exceeds the floor is exactly the unit the floor was not written to
retain). The floor's consequence for T1-F (FFR-2E: the forecast fleet is SHORT, on the cap
segment) is untouched: short ⇒ census ⇒ identical.

### 4.6 The D48 basis, the DR convention, and the FRR carve-out

- **Basis.** The design inherits whichever basis is armed: with `pjm_accreditation_design_
  vintage` on, `A_g` is per-unit UCAP through 2024/25 and the pre-CIFP FPR sets `R`; off,
  ELCC class + composite. D48 §3.3(d)/§8 makes the clearing half the precondition for arming
  the devintage; this design is that precondition, and the A/B carries both arms (§7.6).
  Nothing in D48's measured result changes §3 — it confirms the operands are byte-identical
  across bases (D48 §3.3(a)), so only `A_g` and `R` differ between the arms.
- **DR convention** (D48 §5 item 3, the owner's convention choice): under the D half the
  published OFFERED DR sits in `Q_0` at $0 (no cap applies; the model has no DR cost
  operand). The BRA record clears 76–96 % of offered DR (Table 7: 11,126 of 11,887 … 7,985
  of 10,146), so counting offered DR as a $0 price taker overstates cleared DR by 0.8–2.2 GW
  (0.5–1.3 pts). Rule 13 forbids using cleared DR (an outcome). Under the netting convention
  (D48 D half off) DR is absent from the stack and netted from `R`, and the same ratio
  reading applies. The design works on either; the pre-declaration is stated on both.
- **FRR.** The published curve's x-axis is RPM-only (requirement adjusted for FRR + EE
  addback); the model's stack and requirement are RTO-wide, so cleared MW are NOT
  comparable to Table 6's cleared UCAP — only positions are (PREDECL §2 compares
  positions). The refinement, if a later lane wants MW comparability, is published: BRA
  Table 9 minus Table 7 gives the FRR-committed quantity by resource type per delivery year
  (e.g. coal 53,444 − 44,936 = 8.5 GW UCAP in 2021/22); removing it from both sides is an
  intake, not a parameter.

### 4.7 The D53 sector gate (in flight, not landed)

If D53 partitions the screen to merchant/IPP units, sector-gated units become screen-exempt
and enter the stack as $0 price takers by the §3.2 rule (they are utility-committed capacity
whose exit is IRP-driven; in RPM most of it is also FRR or self-supplied). The design needs
no change; the composition of `Q_0` grows and the offer stack shrinks to the merchant fleet,
which is the reading D32 §4.4 asked for. The build lane states which of D53 / D54 lands
first and pre-declares on the landed posture.

### 4.8 The E&AS offset horizon — one year, not three (named alternative)

PJM's offset is the rolling three-year historical average of net revenues (Att DD §6.8(d));
the screen's operand is the prior-year attainable margin. Decision: **one operand** — the
offer and the exit decision must be the same object, or a unit could clear and still retire
(or fail to clear and stay), breaking §3.5's identity. The three-year form is the one
admissible alternative (zero DOF; the ledgers carry the per-unit history) and its
consequence is named: it would temper the 2024 coal wave's offers (the 2024 dispatch year
put the whole coal fleet at near-zero margin, PREDECL §2) and it would change the screen's
own bar test — a screen-rule question for the retirement lane, not this one.

### 4.9 NYISO — a separate lane, and probably not this design

Rule 25: the gate is generic in form but PJM is the only ISO with a sell-offer BRA in the
registry that this design mirrors; NYISO's spot market literally administers `price =
curve(supplied UCAP)` (D28 §4 — "the one ISO whose real mechanism IS evaluate the curve at
a census quantity"), so its clearing half is a supply-census question (D52's object), not
an offer-stack one. ISO-NE's FCA de-list bids and MISO's PRA offers are stack-like but each
would be its own lane with its own identification (D28 §6.5). The generic gate is per-ISO
(`{iso: bool}`) so a later lane can arm another ISO without touching PJM's cell.

## 5. Rule 13 / rule 14 discipline

**Inputs** (market-design parameters, regenerate forward, respond to conditions): the
must-offer rule, the MSOC form, the UCAP conversion, the vintage VRR curves, the
requirement, the accreditation registries, DR offered series. **Observables** (outcomes,
never targets): BRA Tables 6/7 offered / cleared / uncleared UCAP by type, the Resource
Clearing Price, the cleared position. The design is validated against the observables
(PREDECL §2) and touches none of them.

**Sign (rule 14), stated before any build:** where the model sat in 2022–2024 (position 4–11
pts past the zero-cross) the census paid $0; a faithful clearing pays the marginal offer
where the stack meets the curve — on the committed operands **$82.81 / $82.81 / $157.98 per
MW-day** on the D48 basis ($95.89 / $95.89 / $175.11 on HEAD's) — i.e. MORE than $0 and
MORE than the published $50.00 / $34.13 / $28.92, because the model's stack above the
published price is ~65–80 GW firm where the auction's uncleared was 9–23 GW. Retirements:
the failing set shrinks from 79–92 GW firm to 12–15 GW (the uncleared set), so the
cap-bound coal cohort is retired **LESS** in the years the model over-retired coal (2022
decision → 2024 execution; D48 §3.2's +1.4 GW turns negative), while the zero-E&AS gas
steam fleet — offered at its full bar at the top of the stack — is retired **HARDER** than
the record (2.7 GW actual gas_st exits 2021–2025). The second sign is the E&AS operand's
signature made visible (§6 item 1), reported at full magnitude, and it is NOT a reason to
haircut an offer; the price gap and the steam over-exit are one finding.

**The falsifier.** The design is refused as *tuned* if its build reproduces the published
clearing price (within ±20 %) in any long year on operands that the pre-declaration
instrument says cannot produce it — i.e. any move from the instrument's price toward the
published one must be traced to a named operand change with its own citation (an E&AS
repair, a bar re-identification from source data, the three-year offset) and re-declared,
never to a coefficient. Equally, the design is NOT refused because its price misses the
published one: that miss is the measurement it was built to make.

## 6. What the design does not do, and what it surfaces (stated limits)

1. **The E&AS operand for peakers and steam is the binding defect the design exposes.** In
   every screen year the gas_ct (24.2 GW firm), gas_st (8.8 GW) and oil (3.7 GW) fleets carry
   exactly zero attainable margin (D45 §1 (i)), so their offers sit at their full bars
   (61 / 103 / 76 $/MW-day on the UCAP basis) — a 37 GW plateau above the published price
   in every year. The real fleet earned E&AS (the SOM net-revenue tables) and offered below
   its gross ACR. This is the D12 scarcity-basis object seen from the capacity side: the
   hindcast prices carry no scarcity/reserve rent a peaker lives on. Not this lane's; named
   as the first successor.
2. **Coal's bar level.** The model's coal going-forward cost (45 × 1.3 = $58.5/kW-yr = 160
   $/MW-day nameplate) is 2.0× PJM's published default gross ACR for coal (80 $/MW-day in
   2022/23 $, 94 in 2026/27 $). The bar is rule-23-frozen (identified from ATB/S&L), and the
   design does not touch it; the comparison is recorded because it is the second reason the
   model's stack is dearer than the record (the 2024 coal offers at 140–174 $/MW-day).
3. **Nuclear.** Passes on energy in every year (offers $0); the record's 10.6 / 5.8 GW of
   uncleared nuclear in 2021/22–2022/23 is a MOPR-floor artifact the design does not model
   (§2 item 6).
4. **Grain.** RTO-wide, annual, one clearing per screen year at the delivery year's
   vintage; no LDAs, no seasonal CP segments, no incremental auctions, no three-year-ahead
   timing (the BRA for DY `Y/Y+1` clears in `Y−3` on forward-looking E&AS; the model clears
   at `Y` on `Y−1`'s realized margin — the hindcast's information convention, same as the
   screen's).
5. **FRR / DR quantities** as in §4.6.
6. **Whole-unit marginal convention** (§3.4 rule 4).

## 7. The seam list for the build lane

### 7.1 Gate (one field, generic form, PJM-scoped by registry — rule 25)

`ScenarioConfig.capacity_market_supply_clearing_by_iso: dict[str, bool] | None = None`
(GATED default OFF, sibling of `capacity_market_clearing_by_iso`; `None`/absent ⇒ every ISO
off ⇒ byte-identical). Resolved through one predicate
`resolve_capacity_market_supply_clearing(config, iso)` beside
`resolve_capacity_market_clearing` in `config/capacity_market.py`; requires the curve gate
ON for the ISO (a stack cannot clear against a flat anchor — the predicate returns False
and logs once if the curve gate is off). Registered in `_CACHE_KEY_OPTIONAL_FIELDS` /
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"None"` (`scripts/check_cache_key_registration.py
--base origin/main` green); `validate_parameters.py` entry; `__post_init__` coerces to `None`
in a plain backcast exactly as the curve gate is (keepers byte-identical).

### 7.2 Files and functions

| seam | change | depends on |
|---|---|---|
| `src/market_sim/model/capacity_evolution/adequacy.py` | NEW `clear_capacity_supply_stack(fleet, offers, config, iso, peak, year, ...) -> CapacityClearing` (dataclass: price_usd_per_mw_day, cleared_mw, cleared_position, price_takers_mw, cleared_unit_ids, uncleared_by_fuel, marginal_unit_id, how); builds `Q_0` from the SAME terms `accredited_firm_capacity_mw` sums (refactor the per-term sums into a helper both call so I1 is structural, not tested-only); `R` from `resolve_adequacy_requirement_mw`; curve via `MARKET_DESIGN["PJM"]` + `resolve_demand_curve_vintage` | D48's `accreditation_year` threading; `_thermal_firm_mw` (retirements.py) for `A_g` |
| `src/market_sim/model/capacity_evolution/retirements.py::apply_economic_retirements` | compute `offer_g` from the loop's own `net_revenue` (pre-capacity) and `going_forward_cost`; call the clearing ONCE per screen after the margin loop; set `capacity_revenue_usd` per unit from the clearing (cleared: price × 365 × A_g; uncleared: 0) — the capacity leg moves from inside the per-unit loop to after it (two passes over `margins`, no LP); ledger fields on `margin_detail` (`capacity_offer_usd_per_mw_day`, `capacity_cleared`) | the D48 field for `A_g`; `exempt_unit_ids` for price takers |
| `src/market_sim/runner.py` (≈ lines 1955–2040, the once-per-year position block) | when the supply gate resolves ON, thread the `CapacityClearing` result (or its price) into `evolve_fleet` in place of the bare `curve_reserve_position`; write the `capacity_clearing` ledger block beside the D52 `screen_*` observability fields | `capacity_reserve_position` stays computed (the census position is still the ledger's `capacity_reserve_position` row — additive, nothing renamed) |
| `src/market_sim/model/capacity_evolution/evolve.py::evolve_fleet` | accept/forward the clearing object; pass its price to `apply_economic_new_entry` / storage entry as `reserve_position` does today (price-taker, §4.4) | — |
| `src/market_sim/config/capacity_market.py::MarketDesign.capacity_price_per_firm_mw_yr` | NO change to the curve branch; add a one-line short-circuit: when the caller supplies a `clearing_price_per_firm_mw_yr` (the entry/storage price-taker path) return it. Alternatively thread the price through `reserve_position`'s existing slot as a pre-priced object — the build picks whichever keeps the seam single (rule 19) and documents it | — |
| `tests/unit/model/test_capacity.py` | `TestPjmCapacitySupplyClearing`: I1–I6 of §3.6, the 1-gen/1-zone trivial cases first (testing pattern), the known-answer test on the committed ledgers (I5) | `docs/handoffs/d54/clearing-predecl-2026-09-05.json` |
| `model-methodology-spec.md` §5.2 / §5.9 | the clearing half paragraph (offer form, stack, price, uncleared = failing) | doc-sync after the build |
| `docs/codebase-site/data/mechanism-matrix.js` + every `mechanism-matrix/<ISO>.js` | base row `capacity_market_supply_clearing` (cat capacity, mode F) + a cell in all six shards (`.` for ERCOT/CAISO, `U` NYISO/NEISO/MISO with the §4.9 note, `O` PJM `fc`), the rule-28(c) duty; `scripts/check_mechanism_matrix.py --base origin/main` green | — |
| `scripts/run_capacity_hindcast.py` | `--capacity-market-supply-clearing` (sets the PJM row ON; the D48 flags' pattern) | — |
| `scripts/register_forecast_run.py::VERDICT_MAP` | the suffixed keys of §7.6 | — |

### 7.3 The D48 fields it depends on

`pjm_accreditation_design_vintage` (for `A_g`'s vintage and `R`'s pre-CIFP FPR) and
`pjm_demand_response_supply` (for DR in `Q_0`), both landed default-OFF (PR #4707). The
design reads them through the existing resolvers; it never re-implements them. The primary
A/B arm runs with both ON (D48 §8's named configuration); the isolating arm runs with both
OFF.

### 7.4 Cache-key consequence

Unarmed (`None`): byte-identical, the bare `pjm-t1h` key unmoved (`c6091bd5b62bbc3f` at
D48's HEAD; re-resolved at the build's Phase 0 through `run_capacity_hindcast.build_config`
→ `apply_iso_scenario_defaults` → `cache_key()`, the D45-R / D48 known-answer path). Armed:
a new key per arm, pre-declared in the build's PREDECL §1 before any solve, no collision
with any committed bundle. The D48 keys `bbe13b3f7b659d36` (both), `a0ff4a31b27d2748` (V),
`c79fc92aaaac53cc` (D) are the recognisable single-field neighbours.

### 7.5 Registration and records

`register_forecast_run.py --bundle …` on the FORECAST namespace only, suffixed keys, the
slim committed set of the D45-R / D48 template (`meta.json`, `run_config.json`,
`forecast_verdict.json`, the five `evolution_<year>.json` ledgers carved out of
`.gitignore`, `score.json`, the two `screen_signal_diag_*.npz`), scored
`score_capacity_hindcast.py --bundle` + `--flip-gate-extras` (LOYO) + `forecast_verdict.py
--tier t1h`. Never the bare `pjm-t1h`; never the backcast namespace; the board untouched
(a suffixed probe moves no gate row).

### 7.6 The A/B plan

| leg | posture | run id → suffixed key | purpose |
|---|---|---|---|
| control | HEAD post-D48 (D48 fields OFF, supply clearing OFF) = the bare `pjm-t1h` at the build's HEAD; if the bare key has moved since `c6091bd5b62bbc3f`, re-solve it first (D45-R's rule) | `pjm-2021-2025-realized-t1h` → `pjm-t1h` (existing) | the census evaluation |
| **arm A (primary)** | D48 both fields ON + supply clearing ON | `pjm-2021-2025-realized-t1h-d54-clearing` → `pjm-t1h-d54-clearing` | the configuration D48 §8 names: the consistent basis priced by a faithful clearing |
| arm B (isolating) | D48 fields OFF + supply clearing ON | `pjm-2021-2025-realized-t1h-d54-clearing-headbasis` → `pjm-t1h-d54-clearing-headbasis` | the clearing half alone on HEAD's basis; with `pjm-t1h-d48-devintage` (basis alone) the four-cell factorial is complete |

Recipe otherwise D45-R's: `run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year
2025 --vintage 2020 --fuel-variant realized --entry-screen-diagnostics`, years sequential,
PJM solo (rule 12; 9.6–9.9 GB peak measured by D45-R/D48), ~15–25 min per leg. Zero-solve
Phase 0 first: the build's clearing function on the committed ledgers must reproduce
PREDECL §2 (I5) before any leg launches. Pre-declared expectations per leg: PREDECL §3.

### 7.7 STOP conditions (the build lane halts and routes, never absorbs)

1. Phase 0: the code's clearing on the committed ledgers misses the instrument's price by
   > $1/MW-day or the cleared position by > 0.1 pt in any year → a bug or an operand drift;
   diagnose before any solve.
2. The bare `pjm-t1h` key or any other ISO's default key moves.
3. I2 fails in any solved year (a screened unit cleared and failing, or uncleared and
   passing, beyond the marginal unit) → the settlement is wired wrong.
4. Any arm's clearing price lands within ±20 % of the published price in a long year
   (2022–2024) → the falsifier of §5: stop, find the operand that moved, re-declare.
5. FC-3 moves in 2025 in either arm beyond the entering-fleet consequence of the 2022–2024
   decisions (PREDECL §3 bounds) → a second mechanism is reading the clearing; diagnose.
6. Wall > 2× the control, or peak RSS > 12 GB (the 15 GB host) → stop.
7. Anything beyond the suffixed keys, the PJM shard cell, the matrix row and the tests
   moving.

## 8. Sources fetched this session (sha256), and governance attestation

| label | document | sha256 | bytes |
|---|---|---|---|
| `pjm-manual-18-rev62` | https://www.pjm.com/-/media/DotCom/documents/manuals/m18.ashx (Revision 62, effective 2025-12-17, 289 pp.) | `f188c587d5e00112e5dfa1ab84a793cb335f72bf82b23caa31c488fe8e929bfa` | 1,854,750 |
| `pjm-bra-report-2021-2022` … `2025-2026` | the five BRA reports of D45 §8, re-fetched from the same URLs | identical to D45 §8 (`800e4b3a…`, `ca9d51b9…`, `ef82660e…`, `00ddf7c9…`, `6d47fb09…`) | 492,361 / 844,297 / 585,093 / 762,397 / 1,834,375 |

Committed rows read: `data/raw/capacity-market/{auction-price,auction-supply,demand-curve,
avoidable-cost-rate}/pjm/pjm.csv`; the D45-R (`c6091bd5b62bbc3f`) and D48
(`bbe13b3f7b659d36`) bundle ledgers; `docs/handoffs/d48/devintage-positions-d45r-2026-09-04.json`;
`docs/handoffs/d45/published-positions-2026-09-03.json`.

- **Scope.** Docs only: this design, its pre-declaration, and the zero-solve instrument +
  outputs under `docs/handoffs/d54/`. No `src/`, no `ScenarioConfig` field, no matrix row or
  cell (the build lane's rule-28 duty, listed in §7.2), no solve, no registration, no keeper /
  shard / marker, backcast namespace untouched.
- **Rules 13 / 14.** Every published quantity above is either a market-design parameter the
  registry already carries or a validation observable the pre-declaration compares against;
  nothing is targeted; the signs are stated in §5 before any build.
- **Rule 19.** One offer per unit from one bar and one E&AS operand; one clearing per screen
  year; the failing set is the uncleared set; no second cap, floor, or price seam.
- **Rule 21.** Zero free parameters (§3.7).
- **Rule 22.** T1-H window 2021–2025 only; nothing out-of-training is read; LOYO is the
  build's scorer-side sign test.
- **Rule 25.** PJM's own rules and caps; NYISO's clearing half is a separate lane (§4.9).
- **Rule 27.** Every file this lane pushes is new; blobs verified after push.
- **Collision.** None — D48 owns the PJM surfaces and this lane read its PREDECL and FINDING,
  never its branch.

## 9. Exit

The design and its pre-declaration are pushed. The build is a SEPARATE charter the director
issues; D48 has landed with the recommendation that the devintage be armed WITH this
mechanism, so the build's primary arm is the joint configuration (§7.6 arm A). D48's result
changes nothing in §3–§4; it adds arm B as the isolating control and it sharpens the
pre-declaration's sign on FC-3 (the D48 arm's +1.4 GW of cap-admitted coal is exactly the
cohort a faithful price retains). What the build cannot do without a second charter is
repair the E&AS operand (§6 item 1) — the design will measure it; the repair is the D12
scarcity-basis lane's, and the pre-declaration says what the design's price will read until
that lands.
