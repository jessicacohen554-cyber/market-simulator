# Voluntary clean-energy demand — design memo (SCN-WS3a, 2026-09-05)

**Lane:** SCN-WS3a, plan §3 WS-3 item 1 / §7 "WS-3a" (`docs/handoffs/forecast-scenario-readiness-plan-2026-09.md`),
issued by the Scenario Readiness Desk r#1 (`docs/handoffs/scenario-desk-ledger-2026-09.md` §5,
model rule §5.1). **Memo-first (the FF-0C / FF-G4 pattern). Design only.** No code, no solve,
no default, no `ScenarioConfig` field, no constant, no matrix cell, no test, no scorecard move.
This file is the lane's only deliverable and the only file it touches.

**Head at start:** `origin/main` `5cc1e7ce` (desk pin `d01ab8b0` plus the desk-charter merge
#4853). Branch `claude/scn-ws3a-voluntary-demand-9f1you` off that head. Every `file:line` below
was read at this head, not inherited from the plan (the plan's survey was at `4d4dc6ce`; where
a line moved the current one is cited).

**WS-2a precondition, as found:** `git ls-remote --heads origin` at session start lists **no
`scn-ws2a` branch**. §2 is therefore written against `model/lp/rows.py` **as it stands**, and the
relaxation of its "requires the RPS region family" coupling (`rows.py:1346`, enforced at
`rows.py:1872-1878` and `model/lp/model.py:382-390`) is stated as an **assumed precondition**
that SCN-WS3b inherits from SCN-WS2a, never something this memo designs around twice.

**What this memo is for.** Two desk cards are PRESENTED and OPEN: **D-3** (is a voluntary
clean-demand *scenario axis* admissible at all, given the standing `ffr-5b` §1.4 ruling that
corporate-PPA demand is inadmissible as a *driver*) and **D-6** (the attribute-netting rule
between a voluntary row and a federal CES row). §1 is the brief the owner rules D-3 on; §4.2 is
the brief for D-6. Neither ruling is assumed anywhere below. §7 lists every box that must be
signed before SCN-WS3b can build, in the five-line form the desk asked for.

---

## 0. Bottom line

1. **`ffr-5b` §1.4 was right about a calibrated driver and does not reach a declared scenario
   axis.** Its two grounds — proprietary volume series (rule 13 reproducibility) and no forward
   series at ISO grain (rule 20 free parameter) — are tests of a quantity the model would be
   *tuned against* or *claim as the world*. A scenario axis is neither: its level is an owner
   what-if declared from public anchors, it is coerced inert in every backcast and hindcast so it
   cannot add a degree of freedom to the calibrated model, and its whole purpose is to be moved
   between cases. That is the class `carbon_price_path`, `demand_growth_path`,
   `datacenter_load_path`, `electrification_path`, `tech_cost_path` and the federal CES premium
   already occupy, each admitted on exactly this reasoning (§1). **Recommendation on D-3: YES,
   as a declared, forecast-only, publicly-anchored axis** — with the null `ffr-5b` §5.4 disclosed
   left standing for the calibrated model and every hindcast.
2. **Representation: one annual volumetric clean-attribute row per ISO with a
   willingness-to-pay (WTP) escape column** — the RPS row's exact form (`rows.py:27-103`) with a
   volume RHS instead of a share, the voluntary market's eligible set, and the escape priced at
   the buyer's reservation price instead of a statutory ACP. Dual = the voluntary attribute
   price; reaches entry and retirement through the existing no-stack `max()` seam with zero new
   consumers (`new_entry.py:1450-1483`, `retirements.py:3152-3183`). Hourly (24/7) matching is
   **deferred** to the isolated `scope2-lce-portfolio/` tool with the LP-shape and
   portfolio-problem reasons stated (§2.2); an entry-screen-only price adder is **rejected** —
   no dispatch footprint, and it would re-purpose an existing registered knob (§2.3).
3. **Volume construction, DC-linked:**
   `V(ISO, y) = s_base(ISO, y) × E_nonDC(ISO, y) + f_commit(y) × E_DC(ISO, y)`, where `E_DC` is
   the energy of the existing data-center block (`data/datacenter.py:211-236`) so a high-DC case
   and a high-voluntary case are coherent by construction. Public anchors: NREL's voluntary
   market report (2023 data: 319 million MWh, ≈ 8 % of U.S. retail sales — sourced), the CEBA
   Deal Tracker's public aggregate (150.2 GW since 2014 — sourced, **not ISO-resolved**, exactly
   as `ffr-5b` said), the hyperscalers' published pledges (sourced, and **not monotone** — Meta
   left RE100 in July 2026), and a load-share allocation. §3's table marks every cell
   `SOURCED` or `NEEDS-CITATION`; a `NEEDS-CITATION` cell ships as 0, never as an invented
   number (the DC block's own "no source ⇒ ship 0" rule).
4. **On D-6 the memo disagrees with the plan's recommendation and says why.** The plan §6 row
   recommends "counts toward". On the facts of certificate retirement (one REC, retired once;
   voluntary retirement removes it from the compliance pool), the honest default is
   **"additional"**, represented as one certificate market with two escapes. Both readings are
   expressible through the same field; the campaign reports both; the owner rules (§4.2). D-6
   does **not** block the ERCOT build or probe — ERCOT carries no state attribute row
   (`capacity_market.py:4276`) — it blocks only the `CES-P20+VOL-HI` interaction case.
5. **Nothing here proves anything.** The plan §5.1 / ledger §3 **Voluntary column is left
   UNMOVED** — every cell stays `no` / `—`. A memo earns no row; SCN-WS3b's build moves rows
   1/2/4/5 and SCN-WS3c's probe moves rows 3/7.

---

## 1. The `ffr-5b` §1.4 ruling, line by line — why a declared scenario axis is a different admissibility class (owner box D-3)

`ffr-5b` (`docs/handoffs/ffr-5b-procurement-channel-design-2026-08-05.md`) was chartered under
owner decision D-16(a) to design **a procurement channel for VRE entry** — a step-4 additions
limb whose MW would be *built into the fleet* (§0 items 1–2, `:32-52`). Its §1.4 (`:226-243`)
adjudicates *corporate PPA demand as a candidate volume series for that channel*. The memo
quotes each of its four paragraphs and answers each on its own terms.

### 1.1 "What identifies it. Nothing admissible." (`ffr-5b:228-232`)

> *"The usable volume series (BNEF, LevelTen PPA Price Index, S&P) are proprietary — they cannot
> enter `data/raw/` as a re-queryable source … CEBA's public deal tracker is announcement-grade,
> deal-count-oriented and not resolved to ISO or to an EIA plant identity."*

**Every factual claim here is true and this memo relies on none of the refused sources.** The
CEBA tracker is confirmed public-aggregate-only in this session (150.2 GW cumulative, 19.7 GW
H1-2026; the deal-level download is form-gated; no state or ISO split on the public page —
§3.2). The memo therefore uses CEBA **only for what it publicly is** — a national PPA trend —
and allocates to ISOs by a *different*, public, load-based key (§3.3).

**Where the paragraph does not reach:** "identification" is the demand a *driver* makes. A
driver asserts "this is how much corporate procurement there will be in MISO in 2031", and
rule 13 rightly asks how anyone could regenerate that number from a re-queryable source. A
scenario axis asserts "*suppose* voluntary demand in MISO in 2031 is X" — the number is not
identified from data, it is **declared** by the owner (plan §6 D-2: *"Scenario levels are the
owner's what-ifs by definition; never a modeller's tuning"*), and what rule 13 governs is the
**anchors** the declaration is scaled from. The precedent is exact: the DC block's MW
trajectories are *"ENVELOPE VALUES derived from the published headline figures … each traced
… to its primary ISO forecast / interconnection-queue source with the arithmetic shown"*
(`constants.py:2836-2848`), tagged *"a forward input, not a fitted knob"* (`:2843`), and an ISO
with no published decomposition ships `{}` ⇒ 0 MW (`:2844`; NEISO at `:2925-2945`). §3 applies
that rule cell by cell.

### 1.2 "Forward analogue. None exists." (`ffr-5b:234-237`)

> *"No published forward corporate-procurement volume series exists at ISO grain, so a forward
> number would be a modeller's assumption — a free parameter, refused by rule 20 `[R-DOF]` … and
> by rule 24 the moment it needed a `ScenarioConfig` home."*

This is the paragraph D-3 actually turns on, and it conflates three things.

**(a) Rule 20 refuses a *tuned* value, not a *declared* one.** Rule 20's text is *"a residual
that can only be closed by a tuned value is an open root-cause issue, not a parameter."* A
scenario level is never tuned: it is fixed before any solve, it enters no residual, it is
scored against nothing, and the DOF ledger records its identification as **"Owner"** — the
precedent being FF-G4's ledger row for `electrification_path`'s default
(`ff-g4-load-shape-design-memo-2026-07.md` §7). The federal CES premium is the closest analogue
and was admitted this way: an exogenous $/MWh *"priced by the scenario (an ensemble of premium
levels)"* with a `{10, 20, 30}` ladder set by owner decision D8 (`scenarios.py:3084-3096`) — no
forward series at ISO grain exists for that either.

**(b) The calibrated model's DOF count is unaffected because the axis never enters it.** The
field is coerced inert in `mode="backcast"` **and** in the capacity hindcast (`hindcast=True`),
the exact `datacenter_load_path` construction at `scenarios.py:15739-15746` (*"Forcing it to
'off' keeps every backcast keeper and hindcast BYTE-IDENTICAL"*), with the standalone
defense-in-depth raise pattern of `data/datacenter.py:323-352`. A quantity that cannot reach a
scored keeper, a T1-H hindcast or a T1-X crossover cannot be a fitted degree of freedom in any
of them. Rule 22's own clause says what remains: *"2026 forecast runs are permitted … NOT
restricted."*

**(c) Rule 24 is inverted.** Rule 24 `[R-REGISTRY]` *requires* every solve-affecting tunable to
have a `ScenarioConfig` home visible in `run_config.json`; what it forbids is the *off-registry*
channel. A registered, cited, forecast-only axis is rule 24 satisfied, not rule 24 violated.

**What is conceded:** a forward *level* is a judgment. The memo's discipline is that each level
is arithmetic from a public number with the assumption declared (§3.4), the levels are the
owner's (D-2), and the model is never allowed to prefer one level over another by fit — a
scenario response is never "tuned to look right" (plan §4).

### 1.3 "Its realized half is already inside Candidate A." (`ffr-5b:239-241`)

> *"a corporate PPA that is actually signed produces an interconnection agreement and a
> proposed-generator row. So the channel does not lose the phenomenon — it loses only the
> unsigned part."*

True, and the memo's design **depends** on it rather than contradicting it. The voluntary row
is a *demand-side attribute constraint*; it **never builds anything** (the RPS rows' own
doctrine: *"THE ROWS' ONLY OUTPUT IS A PRICE … a force-build limb would stack against the FFR-5E
procurement channel — the rule-19 failure FFR-5B refused"*, `rows.py:232-234`). A plant that
entered through the EIA-860 pipeline (step 4, `procured_vre_additions` at `runner.py:4500`) and a
plant the merchant screen builds (step 5) both *supply* the row. There is no double count to
net: when the pipeline already covers the volume the row is slack and its dual is zero — a
satisfied buyer pays no premium — which is what today's ERCOT voluntary market looks like
(*"voluntary TX RECs ~$1–3/MWh, immaterial"*, `scenarios.py:8983`, `:9021`). The unsigned part
`ffr-5b` could not observe is exactly the part a scenario is entitled to *posit*.

### 1.4 "Verdict: INADMISSIBLE. This is where the null bites (§5.4)." (`ffr-5b:243`, `:560-573`)

The null — *"a part of D-16's gap has no admissible representation at all, and this lane's honest
answer is to disclose it rather than invent a driver for it"* — **stands, unamended, for the
calibrated model and for every hindcast.** This memo does not propose to fill that gap in the
backcast, the T1-H hindcast or the T1-X crossover; the axis is off in all three by construction
(§5.2), so the disclosed residual behind under-built MISO/PJM solar
(`ffr-3v-miso-entry-screen-2026-08-04.md:64,410,818`) keeps its size and its label. What the
axis adds is the ability to ask, in a forecast, *"what if that channel is this big"* — which is
a question, not a fit. `ffr-5b` itself did not decide this: its §6 (`:576-608`) lists what it
did not decide, and scenario-axis admissibility is outside its D-16(a) charter entirely.

### 1.5 The test, restated for the owner

| Rule 13's question | Calibrated driver (what `ffr-5b` refused) | Declared scenario axis (this memo) |
|---|---|---|
| Could the quantity be produced for a forward year from forward drivers? | No — no public forward series at ISO grain | Yes — it *is* a forward driver: a declared level scaled from public anchors, the `datacenter_load_path` construction |
| Would it respond to changed conditions? | Only if re-fitted | By design: it is the condition being changed |
| Is it a measured outcome fed back in? | The risk `ffr-5b` guarded against | Impossible: coerced off in every mode that is scored against actuals |
| Does it introduce a fitted quantity (rule 20)? | Yes — the free parameter | No — an owner-declared level, ledgered as "Owner"; the model never selects among levels by fit |
| Registry home (rule 24)? | Refused as an off-registry answer key | Required: `ScenarioConfig` field + `run_config.json`, cache-registered at `off` |

**The distinction in one sentence:** a driver's value claims to be the world and must be
identified; an axis's value claims to be a question and must only be disclosed, public in its
anchors, and unable to touch anything that is scored.

---

## 2. Representation options, each against rules 1, 2 and 19

### 2.1 Option A — annual volumetric attribute row with a WTP escape (RECOMMENDED)

**Form.** One `≥` row per ISO-year:

```
Σ_t Σ_{z} (W[z,t] + S[z,t]) + Σ_t Σ_{g ∈ eligible} P[g,t] + Σ_t ESC_vol[t]  ≥  V(ISO, y)
objective:  + WTP × Σ_t ESC_vol[t]
```

This is `_build_rps_row` (`rows.py:27-103`) with three substitutions and nothing else:

| Element | RPS row today | Voluntary row |
|---|---|---|
| LHS wind/solar zone columns | `rows.py:76-77` | identical |
| LHS thermal-block eligible classes | `_resolve_rps_eligible_gen_idx`, `rows.py:104-143` (wind/solar base + statute names; nuclear refused by name, `:56-64`) | same resolver for a renewable-only set; `_resolve_clean_region_gen_idx` (`rows.py:145-202`, nuclear ADMITTED) if the owner admits nuclear/CCS (§4.1) |
| Escape column | the ACP column block, one non-negative variable per row per hour (`layout.py:71-84`, `_rec_acp_off :199-206`), `+1` in the row (`rows.py:84-88`), priced in the objective at the ACP (`costs.py:255-261`) | identical mechanics; the price is the buyer's **WTP ceiling**, not a statutory ACP |
| RHS | `rps_target × Σ demand` (`rows.py:94`) | a **volume** `V(ISO, y)` in MWh (§3) |
| Dual | `DispatchResult.rps_shadow_price` (`lp/__init__.py:138`), read end-anchored at `model.py:1196-1211` | a new `voluntary_attribute_price`, read the same way |

**Zero new builder code is needed for the row itself.** The K-row generalization
`_build_rps_region_rows` (`rows.py:205-295`) takes a `(K, n_zones)` mask and `obligation_frac`
and computes `rhs = frac @ zone_annual` (`:292`); with `K = 1`, mask = all zones and
`frac[0, :] = V / Σ_z zone_annual`, the RHS is exactly `V` and the row is the ISO-wide row
byte-for-byte (the `K = 1, mask = all zones` identity is already regression-tested,
`rows.py:228-230`). The per-zone buyer grain (a DC-zone-matched voluntary region) is then a
data change to the mask, not a code change — deferred, §7 M-8.

**What SCN-WS3b must actually touch (the honest list).**

1. **Row-family selection at `rows.py:1823-1885` and the mirrored count/guard block at
   `model.py:365-402`.** Today the families are an `if / elif / elif` chain: K-row RPS (with the
   clean family nested inside it), *or* the single RPS row; the clean family *raises* without the
   region family (`rows.py:1872-1878`, `model.py:382-390` — the G-S3 coupling, `rows.py:1346`).
   The voluntary row must stand **beside any of the three postures and beside none** — ERCOT
   has no RPS row at all (`STATE_RPS_FLOORS["ERCOT"]` all-zero, `capacity_market.py:4276`; no
   ACP entry, `:4500-4506`; hence `n_rps_rows = 0`, `n_rec_acp = 0` at `model.py:374-375`).
   **Assumed precondition:** SCN-WS2a's relaxation lands first (ledger §4: WS-3b is rows.py's
   next writer *after* WS-2a merges) and turns the chain into independently-armable families
   sharing one ACP block; the voluntary family is then the third such family, appended after
   the federal row. If WS-2a's shape differs, WS-3b writes against what merged, not this table.
2. **The end-anchored dual arithmetic** — the one delicate seam. Duals are located by counting
   back from the reserve tail: `rps_start = size − (reserve + clean + rps)` (`model.py:1197-1198`),
   `clean_start = size − (reserve + clean)` (`:1215`), and the mass-cap offset adds both
   (`:1229-1231`). A fourth family means a `_n_vol_rows` term in every one of those expressions
   and in the ACP slot accounting (`n_rec_acp += n_clean_rows`, `model.py:402`; the clean
   family's `acp_k0 = k_regions`, `rows.py:1857`). The escape-price vector handed to
   `costs.py:255-261` (`rps_acp_price`, shape `(n_rec_acp,)`) must carry the WTP in the
   voluntary slots — the `clean_region_acp_price` concatenation at `model.py:754-758` is the
   pattern.
3. **The consumer side — no new consumer.** The dual rides `PriorYearResults`
   (`pipeline/prior.py:111` is where `clean_attribute_price_by_fuel` lives; `runner.py:4504-4520`
   populates both existing attribute prices) into `evolve_fleet` (`evolve.py:91-92`, `:655-656`,
   `:857-858`) and enters the **existing** `max()`:
   - entry: `effective_attribute_price = max(effective_eac_price_for_tech(...), rps_for_tech,
     clean_for_tech)` (`new_entry.py:1479-1483`), ledgered as `attribute_price` (`:1565`);
   - retirement: `compute_attribute_revenue(..., eac_price, max(rps_for_unit, clean_for_unit))`
     (`retirements.py:3181-3183`; the doctrine at `:374-393`).
   The voluntary dual is one more argument to those two `max()` calls, fuel- and zone-resolved
   through the same helper family (`policy/rps.py:143-180`, `policy/clean_tiers.py:178-195`).
   In dispatch nothing is credited at all — the row is a constraint, and the attribute value is
   the dual, never an offer adder.

**Against rule 1 `[R-STRUCT]`.** This is the real mechanism. A voluntary buyer is a *quantity*
demand with a *reservation price*: it retires certificates up to its commitment and stops
when the certificate costs more than the claim is worth. The row's dual is the marginal cost
of the last eligible MWh the market must produce — un-curtail first (a dumped MWh costs
nothing to redirect), then displace thermal — capped at WTP by the escape, which is how a
voluntary REC/PPA premium clears when supply is short. At low volumes the row is slack and the
price is ≈ 0: the ERCOT voluntary REC at $1–3/MWh (`scenarios.py:8983`) is that regime, so the
mechanism's inertness at today's volumes is the mechanism matching reality, not a defect.

**Against rule 2 `[R-VECTOR]`.** A pure column-append on the existing `arange` expressions
(`rows.py:269-284`); the only Python loop is over `K ≤ 6` regions, never hours.

**Against rule 19 `[R-ONE-MECH]`.** One phenomenon (voluntary attribute demand), one row, one
dual, entering the one attribute-composition seam by `max()` — never a sum
(`policy/eac.py:11-17`: *"each MWh of clean generation produces one attribute certificate, sold
once to whichever buyer clears higher"*). The dispatch-side coexistence with a state RPS row or
a federal CES row is the D-6 question (§4.2); the RPS + clean precedent is already adjudicated
(*"A wind MWh satisfying both its renewable row and its clean row is CORRECT — two constraints,
one MWh"*, `rows.py:1846-1850`), and §4.2 says when that precedent applies and when it does not.

### 2.2 Option B — hourly-matched (24/7) T-row block (DEFERRED; owner box D-3b)

**Form.** Per buyer `b`, per hour: `Σ_{eligible} X[·,t] (+ storage) + ESC_b[t] ≥ L_b[t]`, i.e.
`8760 × B` rows, `8760 × B` escape columns, and a buyer load profile `L_b`.

**Why it is deferred, in three reasons that are structural rather than effort:**

1. **It changes the dispatch LP's shape.** Every existing row family is either per-hour-per-zone
   (energy balance, storage) or annual (RPS, clean, mass cap, oil budget); an hourly attribute
   block is a *third* kind — per-hour-per-buyer — whose duals form an entire hourly price surface
   (an hourly CFE premium) that no consumer downstream reads, and whose escape columns enter
   `vars_per_hour` (`layout.py:102-113`) for every hour whether or not a buyer exists. That is
   not a family the K-row machinery expresses, and it is not byte-identical-off without new
   layout code.
2. **It is a portfolio problem, and the LP's supply columns are not a buyer's.** `W[z,t]` /
   `S[z,t]` are zone aggregates with no vintage or owner (`rows.py:98-101`, `layout.py:212-219`: no additionality mask
   exists in dispatch), and storage columns are system storage. "The buyer's hourly CFE" needs an
   attribution of *which* MWh and *whose* battery — which is the portfolio-selection problem the
   isolated tool already solves: *"selects a portfolio of clean & low-carbon energy resources
   plus storage to match a company/facility 8760 load hour-by-hour, at the lowest cost premium
   above wholesale"* (`scope2-lce-portfolio/README.md:3-9`), consuming *"the market simulator's
   output (BAU hourly LMPs) as an input file"* (`:14-19`), with an explicit isolation boundary
   (`docs/scope2-lce-portfolio.md`: *"no `import market_sim` anywhere"*).
3. **The annual row already carries the deployment signal the campaign needs.** The
   hyperscalers' 24/7 pledges (§3.2) raise the *volume* and the *WTP* of annual-matched demand
   in the model's terms; the hourly shape of that demand is what the portfolio tool prices on
   top of the scenario LMPs.

**Recommendation:** keep 24/7 in the tool. The campaign hands it each scenario's hourly LMPs
(the tool's designed input) and reports the CFE-vs-premium frontier beside the annual row's
dual. An in-LP hourly row is filed as D-3b (§7 M-2) and is not designed here.

### 2.3 Option C — entry-screen-only price adder (REJECTED)

**Form.** Add a voluntary $/MWh to `eac_price_wind` / `eac_price_solar` / `eac_price_geothermal`
(`scenarios.py:3063-3074`) or a new scalar composed into `effective_eac_price_for_tech`.

**Why it fails, against the three rules:**

- **Rule 1:** it is a supply-side subsidy, not a demand. It has no volume, so it never
  saturates, never turns off when the pledge is met, and never prices scarcity of the attribute.
  And it *does* reach dispatch — as an offer credit that lowers wind/solar marginal cost
  (`eac.py:118-165`, `apply_eac_to_mc :50`) — which is the wrong footprint: curtailment would fall
  because offers went negative, not because anyone bought the MWh. The charter's phrase "no
  dispatch footprint" is exact in the sense that matters: **no footprint of demand**.
- **Rule 19:** it re-purposes a registered knob whose documented meaning is a state ZEC/REC
  *contract* price (`eac.py:1-17`), so the `max()` at `eac.py:152-160` could no longer tell a
  state contract from a voluntary buyer, and the CES premium composition
  (`federal_ces.py:397-506`) would silently absorb it.
- **Rule 2 is untouched (no rows),** which is the tell: a mechanism that adds no constraint
  cannot represent a quantity commitment.

**Rejected.** Recorded so no later lane reaches for it as the "cheap" version.

### 2.4 Verdict

| Option | Dispatch footprint | Deployment footprint | New consumer? | Rule 1 | Rule 2 | Rule 19 | Verdict |
|---|---|---|---|---|---|---|---|
| A annual volumetric row + WTP escape | constraint; curtailment first, then thermal displacement; dual ≤ WTP | via `max()` at entry + retirement | none | real market form | column-append | one row, one dual, `max()` | **RECOMMENDED** |
| B hourly T-row block | per-hour-per-buyer rows; hourly premium surface | none read | new hourly price consumer | real, but a portfolio problem | new layout kind | new phenomenon class | **DEFERRED → portfolio tool (D-3b)** |
| C entry-only price adder | offer credit (wrong sign of mechanism) | via `max()` | none | subsidy, not demand | no rows | re-purposes a registered knob | **REJECTED** |

---

## 3. The DC-linked volume construction and its public anchors

### 3.1 Construction

```
V(ISO, y) = s_base(ISO, y) × E_nonDC(ISO, y)  +  f_commit(y) × E_DC(ISO, y)

E_DC(ISO, y)    = Σ_z datacenter_block_mw_by_zone(config, ISO, y)[z] × 8760
                  (data/datacenter.py:211-236; resolve_datacenter_mw :105-151;
                   0 when datacenter_load_path == "off" or the ISO ships {})
E_nonDC(ISO, y) = Σ_{z,t} year_demand[z,t] − E_DC(ISO, y)
                  (year_demand AFTER add_load_layers, runner.py:1956-1957 — the same
                   array peak_demand is taken from at :1958, so every capacity screen
                   and the row see one load)
```

Both halves are resolved in a new `policy/voluntary_demand.py` (SCN-WS3b's file) from
`constants.py` tables under the `datacenter_load_path` grammar: a path label selects
`(s_base, f_commit)` curves, piecewise-linear between knots and edge-held, via the same
`_effective_percentile` / `_interpolate_low_mid_high` helpers `datacenter.py:66-69` imports
(re-exported from `config/scenario_resolvers` at `scenarios.py:27-35`). `off` ⇒ `V = 0` ⇒ no
row, byte-identical.

**Why the DC half rides the DC block rather than its own MW table.** The reason voluntary demand
is *growing* is the hyperscalers' pledges (§3.2), and the reason it is growing *where* it is
growing is DC siting. Linking `V` to `E_DC` makes `LOAD-HI` (DC `high`) and `VOL-HI` coherent
without a second siting table (rule 19), and makes a `datacenter_load_path: off` case carry zero
DC-linked voluntary demand instead of a stranded number. It also inherits the DC block's own
caveats verbatim: NEISO ships `{}` so its DC half is 0 (`constants.py:2925-2945`), and the `low`
paths are 0 in every ISO (`:2867-2874`, `:2879-2882`), so a `low` voluntary path's DC half is 0
by construction.

### 3.2 Anchors — per-cell provenance

Verified in this session over the proxy (NREL's `docs.nrel.gov` does not resolve from this
container; OSTI and CEBA do). `SOURCED` = a public, re-queryable number read this session;
`NEEDS-CITATION` = the cell's source is named but the number was not read here, or the source
does not publish it at the grain needed. **A `NEEDS-CITATION` cell ships as 0 / the fallback
named in its row — never as an invented value** (the DC block's rule, `constants.py:2844`).

| Cell | Value / status | Source | Provenance |
|---|---|---|---|
| National voluntary volume, 2023 | **319 million MWh**, ≈ **9.7 million** customers, **+17 %** over 2022 (⇒ 2022 ≈ 273 million MWh by arithmetic) | O'Shaughnessy, Jena, Salyer, *Status and Trends in the U.S. Voluntary Power Market: 2023 Data*, NREL/TP-6A20-92289, Aug 2025, DOI 10.2172/2584242 | **SOURCED** (OSTI abstract) |
| National voluntary share of retail sales, 2023 | **≈ 8 %** of all U.S. retail electricity sales; ≈ 44 % of non-hydro renewable sales | same report | **SOURCED** — this is `s_base`'s national level |
| Product breakdown (PPAs / utility green pricing / utility contracts / competitive suppliers / unbundled RECs / CCAs), 2023 | in the report's data tables; the abstract notes long-term contracts "likely exceeded" near-term transactions for the first time in 2023 | same report, public data tables at nrel.gov/analysis/green-power | **NEEDS-CITATION** (PDF unreachable through the proxy this session; public) |
| State-level voluntary volumes | published for utility programs and PPAs by state in the same series | same report | **NEEDS-CITATION** — the preferred per-ISO key once read; until then §3.3's allocation |
| Corporate PPA trend | **150.2 GW** cumulative since 2014 (Jan–Jun 2026 update); **19.7 GW** H1-2026; **27.3 GW** in 2025; **21.7 GW** in 2024 | CEBA Deal Tracker public page + CEBA press releases | **SOURCED** as a national aggregate; **NOT ISO-resolved** (deal-level data is form-gated) — used for the growth *shape* of `s_base`, never for allocation |
| Hyperscaler pledges (drive `f_commit`) | Google 24/7 CFE by 2030 (pledged 2020); Microsoft 100/100/0 by 2030; Amazon 100 % annual matching reached 2023; Meta 100 % annual matching since 2020 **but exited RE100 in July 2026 while backing gas plants** | company sustainability pages; TechCrunch 2026-07-23 for the Meta exit | **SOURCED** — and the Meta exit is the evidence that `f_commit` is **not monotone**, which is why the `low` path carries a *falling* fraction |
| Hyperscaler share of DC energy (the weight on `f_commit`) | hyperscale vs colocation vs enterprise split | LBNL 2024 U.S. Data Center Energy Usage Report (Shehabi et al., Dec 2024 — already the citation for `datacenter_load_factor`, `scenarios.py:2864-2866`) | **NEEDS-CITATION** (split not read here) |
| DC block energy `E_DC` | per-ISO low/mid/high MW trajectories | `constants.DATACENTER_ADDITIONS_MW` (`:2858-2950`), each row cited | **SOURCED** (inherited, with each ISO's own caveat) |
| ISO allocation key for the non-DC half | commercial + industrial retail sales share by ISO | EIA-861 — **no `eia-861` datatype exists in `data/raw/`** (`ls data/raw` this session); the repo's only EIA-861 numbers are hand-copied 2023 retail-sales shares in comments (`capacity_market.py:4418`, `:4591-4592`) | **NEEDS-INTAKE** (§3.3 fallback: national share applied uniformly, zone `load_share`) |
| Procurement *location* vs buyer *load* | Texas / ERCOT hosts the largest share of corporate PPAs by project location | CEBA state ranking; NREL state tables | **NEEDS-CITATION** — disclosed as the alternative allocation basis (§3.3), not used |
| WTP ceiling | voluntary unbundled RECs ≈ $1–3/MWh (ERCOT, today, slack regime); PPA premiums are not public per deal | `scenarios.py:8983`, `:9021`; state ACPs $30–50 as the *upper* bracket (`capacity_market.py:4500-4506`); MISO's deliberately-low $30 clean escape proxy as a precedent for a ceiling proxy (`:4701-4707`) | **NEEDS-CITATION** for the level → owner box D-2 / M-5; a ladder, not a point |

### 3.3 Allocation to ISOs (the non-DC half)

`s_base` is national at source. Two keys exist; the memo recommends the first:

1. **Buyer-load basis (recommended).** Apply the national share uniformly to each ISO's non-DC
   energy (i.e., `s_base(ISO) = s_base_national`) until the EIA-861 commercial-sector shares
   are intaken, then scale by `(ISO commercial share) / (national commercial share)`. Within an
   ISO the row is ISO-wide, so no zone split is needed at all; if a per-zone grain is ever wanted
   (M-8) the DC-block default applies — `iso_configs` zone `load_share`
   (`data/datacenter.py:190-207`; ERCOT's at `iso_configs.py:193-199`), never an invented split.
   Reproducible from public data; responds to load growth by construction.
2. **Procurement-location basis (disclosed, not used).** Corporate PPAs concentrate by
   *project* location (Texas first), so ERCOT's *certificate* demand from out-of-ISO buyers
   exceeds its in-ISO buyer load. That is real, but the only public number is a state ranking
   (`NEEDS-CITATION`), the deal-level split is gated, and using it would attribute PJM buyers'
   demand to ERCOT's row — a cross-ISO transfer of a fitted-looking number (rule 25). If the
   owner wants it, it is a second path label, not a hidden reweighting.

**Rule 25 `[R-ISO-SCOPE]` posture:** no ISO's fitted value crosses a boundary; a national public
number allocated by a public key is a shared anchor, the same class as `DEMAND_GROWTH_RATES`'
per-ISO rows or the RFF carbon paths.

### 3.4 Levels — illustrative until owner box D-2

Each level is arithmetic from a `SOURCED` cell with its one assumption stated. None is a
recommendation of what the world will do; they are the three what-ifs the campaign runs.

| Path | `s_base` (non-DC share) | `f_commit` (fraction of DC energy under a clean pledge) | WTP ($/MWh, real-2026 per `constants.REAL_DOLLAR_BASE_YEAR`, `constants.py:1842`) |
|---|---|---|---|
| `off` | 0 (no row) | 0 | — |
| `low` | hold the 2023 national share flat: **0.08** every year | **0.5** falling to **0.4** by 2035 (the Meta-exit reading: pledges erode as gas-backed DC growth outruns procurement) | **5** |
| `mid` | grow at half the 2022→2023 rate (≈ 8 %/yr) from 0.08 (2023) to a 2030 knot ≈ **0.14**, hold | **0.75** flat | **10** |
| `high` | grow at the 2022→2023 rate (17 %/yr) to a 2030 knot ≈ **0.24**, hold | **1.0** flat (every DC MWh annually matched — the Amazon/Microsoft 2023–2025 posture applied to the whole block) | **20** |

The WTP column is a ladder in the CES-premium sense (`{10, 20, 30}` under D8), bracketed *below*
the state ACPs ($30–50) because a voluntary buyer's reservation price is by definition the
price at which it declines the claim, and today's unbundled voluntary REC clears near zero; the
`mid` point is the cell most in need of an owner number (§7 M-5).

**DOF ledger sketch (rule 20/21 — what SCN-WS3b must pin):**

| Parameter | Identification source | Open DOF? |
|---|---|---|
| `s_base` national level 2023 | NREL 2023 data (SOURCED) | No — cited; re-derives on a new NREL edition only (rule 23) |
| `s_base` growth knots per path | arithmetic on the SOURCED 2022→2023 rate, assumption declared | **Owner (D-2)** — a scenario level, never fitted |
| `f_commit` per path | public pledges (SOURCED) × hyperscaler share of DC energy (NEEDS-CITATION) | **Owner (D-2)**; the weight ships 0 until cited |
| `E_DC` | inherited `DATACENTER_ADDITIONS_MW` | No (already ledgered) |
| ISO allocation key | uniform national share → EIA-861 commercial share on intake | No — public data; the intake is box M-6 |
| WTP ceiling ladder | bracket from public REC/ACP levels; level is the owner's | **Owner (D-2)** |
| Eligible fuel set | market definition (RE100 / Green-e renewable vs 24/7 "carbon-free") | **Owner (M-4)** |
| Netting rule | policy design | **Owner (D-6)** |

No parameter anywhere is identified from a model residual; a scenario response that "looks
wrong" is a finding for the capx queue, never a level edit (rules 1/11/13/14).

---

## 4. Eligibility, and the netting rule against a federal CES

### 4.1 Eligibility

**Default: the voluntary *renewable* market's set — `wind`, `solar`, `geothermal`,
`offshore_wind`**, resolved exactly as the RPS row resolves statute names: wind/solar are the
zone columns, the rest resolve through `FUEL_TYPE_MAP` to thermal-block generator columns
(`_resolve_rps_eligible_gen_idx`, `rows.py:104-143`; the `RPS_ELIGIBLE_FUELS_BY_ISO` data
pattern at `capacity_market.py:4554`). An unknown name hard-errors, never silently drops
(`rows.py:134-138`). Storage discharge is **ineligible** (no new attribute is created by
discharging — the `federal_ces_storage_eligible=False` doctrine, `scenarios.py:3148-3150`).

**Owner box (M-4): admit `nuclear` and `gas_cc_ccs` for "carbon-free" programs?** The
24/7-CFE pledges count nuclear and geothermal (Google) and "zero-carbon" supply (Microsoft), and
the CEBA tracker's eligible technologies include nuclear, geothermal and CCS. If admitted, the
row uses the clean-family resolver (`_resolve_clean_region_gen_idx`, `rows.py:145-202` — the one
resolver that admits nuclear, by design the *"deliberate difference from the renewable
resolver"*) with `gas_cc_ccs` credited at 1.0 (a certificate, not a capture fraction — the
`clean_capture` crediting question belongs to the CES row, not here). Recommendation:
**renewable-only default, carbon-free as a second path label** (`voluntary_eligible_fuels` is a
field either way), because the SOURCED volume anchor (NREL "green power") is a renewable
definition and admitting nuclear against it would over-credit the same volume. The §45U
composition for nuclear is settled and does not re-open (D-28 option A, `retirements.py:3186+`).

**No additionality mask in dispatch, ever.** The LP's W/S columns carry no vintage
(`rows.py:98-101`, `layout.py:212-219`); annual REC matching has no additionality either. If the owner wants
additionality it is an *entry-screen* rule — voluntary value credited to new builds only, i.e.,
the voluntary dual enters `new_entry.py`'s `max()` but not `retirements.py`'s. Filed inside M-4,
not recommended (it would make the retirement screen blind to a real revenue).

### 4.2 The netting rule — owner box D-6, argued

**The question.** When a federal CES row (SCN-WS2a) or a state RPS row and a voluntary row
coexist in one ISO-year, does a voluntary buyer's MWh *also* satisfy the standard
("counts toward") or must the standard be met by *other* MWh ("additional")?

**What the two readings are in the LP.**

| Reading | Rows | Escape | Dual(s) | When the voluntary row matters |
|---|---|---|---|---|
| **counts toward** | two independent `≥` rows, the same MWh in both LHS | each row its own (ACP; WTP) | two duals; entry sees `max()` | only where `V` exceeds what the standard already compels — ERCOT (no standard), or a high path |
| **additional** | **one** row: `Σ eligible + ESC_ces + ESC_vol ≥ target × load + V` (the voluntary volume is *added to the standard's RHS*, both escapes `+1`) | two escapes on one row | **one** dual, capped at `min(ACP, WTP)` — the cheaper escape fires first | always: the voluntary buyer competes with compliance buyers for the same certificates |

**The facts favour "additional".** A certificate is retired once. A REC retired for a voluntary
claim is removed from the pool a load-serving entity could retire for compliance; the Green-e
Energy standard and the state RPS rules it interoperates with prohibit using the same REC for a
voluntary claim *and* compliance (`NEEDS-CITATION`: Green-e Energy National Standard, double-
claiming prohibition; the plan §4 states the same one-MWh-one-claim principle). So the market
the model should reproduce is **one** certificate market in which voluntary and compliance
buyers compete, and in which the voluntary buyer — whose reservation price is below the ACP —
**drops out first** when certificates are short. That is exactly what the single-row two-escape
form does: the LP fires the cheaper escape (`ESC_vol` at WTP) before the dearer (`ESC_ces` at
ACP), so the voluntary claim is forgone before the LSE pays the penalty, and the one dual is the
one REC price both buyers face. "Counts toward" instead lets a compliance-compelled MWh be sold
twice (once to the LSE's obligation, once to the voluntary buyer at a zero premium), which is
the double claim the plan §4 says the campaign must not make.

**Where "counts toward" is nevertheless right.** Where the *standard's own design* credits
customer-side voluntary purchases toward the LSE's obligation (some green-tariff constructions
do), or for the RPS + clean-tier precedent (`rows.py:1846-1850`) — but that precedent is two
*obligations* on one MWh imposed by two statutes, not a voluntary buyer and an obligation
competing for one certificate. The distinction is why the memo does not simply inherit the
precedent.

**Why the plan's row said "counts toward".** Its stated reason — *"matches how RECs retire
today"* — is the reverse of the retirement fact above; the memo reads it as a slip and flags it
rather than following it. The plan's operative instruction, *"Report both"*, stands.

**Recommendation on D-6: default `additional`; the field expresses both; the campaign reports
`CES-P20+VOL-HI` both ways** (plan §3.5). Note the CES *premium* ladder (`CES-P10/20/30`) has no
row and no netting question at all — a premium composes by `max()` at entry and as an offer
credit in dispatch; D-6 bites only against the CES *target* row (`CES-T80`) and the state RPS
rows. **D-6 therefore blocks neither SCN-WS3b's build nor SCN-WS3c's ERCOT probe** — ERCOT has
no state row and REF carries no federal row — it blocks the interaction case only.

**Interaction with `federal_ces_replaces_state_rps`** (`runner.py:2851`, `federal_ces.py:508`):
the pure-federal counterfactual suppresses *state* rows; the voluntary row is not a state
instrument and is **not** suppressed by it. Stated as a design decision for WS-3b.

---

## 5. Fields, coercion, cache key, matrix duty (the registry surface — rule 24)

The plan budgets ≤ 3 fields. The memo needs a fourth if D-6 rules "report both"; §7 M-7 routes
that to the desk.

| Field | Type / default | Grammar | Registered where |
|---|---|---|---|
| `voluntary_clean_demand_path` | `str = "off"` | `"off" \| "low" \| "mid" \| "high"` — the `datacenter_load_path` grammar (`scenarios.py:2843`, `datacenter.py:76-79`); the single field is both gate and level selector (the `electrification_path` collapse, `:2874-2894`) | `_CACHE_KEY_OPTIONAL_FIELDS` (`scenarios.py:148`) + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` (`:1429-1480`) at `"off"`, same commit; `TIER_TAGS` (`:17022`, the DC fields' `2` at `:17049`) |
| `voluntary_wtp_ceiling_usd_per_mwh` | `float` (real-2026 $/MWh; default = the `mid` ladder point once D-2 signs) | scalar; inert when the path is `off` | both cache registries at its default |
| `voluntary_eligible_fuels` | `list[str]`, default `["wind", "solar", "geothermal", "offshore_wind"]` | `FUEL_TYPE_MAP` names (the `federal_ces_eligible_fuels` pattern, `:3128-3137`) | both cache registries at the default list |
| `voluntary_netting` *(if D-6 = report both)* | `str = "additional"` | `"additional" \| "counts_toward"` | both cache registries at the default |

**Coercion (§5.2).** In `__post_init__` (`scenarios.py:15468`): validate the label, then
`if self.mode == "backcast" or self.hindcast: self.voluntary_clean_demand_path = "off"` — the
verbatim `datacenter_load_path` block at `:15739-15746`. The other fields are **not** coerced
(they are inert with the path off and are cache-neutral at their defaults) — and where any
coercion is written it coerces **to the dataclass default, never to a literal**
(`:15765-15790`'s FFR-3D rule; the measured re-keying it prevents is recorded there). The
standalone `validate_voluntary_config` in `policy/voluntary_demand.py` raises on a non-`off`
path reaching a scored backcast (defense in depth, `datacenter.py:323-352`). The hindcast
coercion is a deliberate choice, stated: T1-H (2021–2025) and T1-X (2023–2027) pin realized
load and score against actuals, so the axis is off there exactly as the DC block is
(`:15728-15737`); a forward-year voluntary volume inside a scored window would be the fed-back
outcome rule 13 forbids.

**Cache key.** Registration at the default keeps every backcast keeper key, every hindcast key
and the shipped forecast key byte-identical; an armed path hashes distinctly (the field enters
the hash at a non-default). `scripts/check_cache_key_registration.py` checks 1–3 enforce
registration + declared default in the same PR. **Deliverable for WS-3b: list the keeper keys
before/after and show them unchanged** (plan §7 WS-3b).

**Row/layout identity when `off`.** `V = 0` ⇒ no row, no ACP slot, `n_rec_acp` unchanged, LP
byte-identical — the `rps_target is None` convention (`model.py:374-375`). A `low`/`mid`/`high`
path with a `V` that the fleet already exceeds still emits the row (slack, dual 0) so the row
count is a function of the config alone, never of the year (`policy/rps.py:101-104`'s rule).

**Matrix duty (rule 28).** SCN-WS3b's PR — the one that creates the field — mints the base row
`voluntary_clean_demand` (`cat: "policy"`, `mode: "F"`) in `docs/codebase-site/data/mechanism-
matrix.js` beside `rps_lp_constraint` (`:2554`) / `federal_ces` (`:2574`) / `datacenter_load_block`
(`:2532`), **plus one cell line in every ISO shard** (`U` in ERCOT/CAISO/PJM/MISO/NYISO; NEISO
`U` too — its DC half is 0 but the non-DC half is live) as the **last commit** after a
fetch+rebase (ledger §4 protocol item 2; ERCOT's cell lines at `mechanism-matrix/ERCOT.js:303-309`
are the format). `scripts/check_mechanism_matrix.py --base` fails the PR otherwise (`:33-44`).
This memo mints nothing (a design lane adjudicates nothing — `ffr-5b` §6's same discharge).

**Registry visibility.** All fields echo to `run_config.json` (rule 24); no env-var, no
CLI-only knob; the campaign expresses `VOL-MID` / `VOL-HI` as one-field overrides on REF
(plan §3.5).

**Docs SCN-WS3b owes:** `docs/codebase/05-policy.md` (a §5.2-style subsection), the spec's
policy section, and the CHANGELOG — via `/sync-docs` when the build settles.

---

## 6. Probe design (for SCN-WS3c) and its structural gate

**Tier and vehicle.** ERCOT 2026 **T0** (FF plan §2.1: 1–3 solve-years, minutes; ERCOT
~3–8 min/yr) — REF vs `VOL-MID`, then ERCOT **T1-F 2026–2030** REF / `VOL-MID` / `VOL-HI` for
the entry-wave response. Five solve-years per invocation: §2.1b-clean, no full-horizon, no
grant needed. Paired construction through the golden-recipe-±-one-signal harness: add
`"vol_mid": {"voluntary_clean_demand_path": "mid"}` (and `vol_high`) to
`PAIRED_ARM_OVERRIDES` (`scripts/run_driver_battery.py:1042-1047`; `run_paired_arm :1050`).

**Why ERCOT.** No state RPS row (`capacity_market.py:4276`), no ACP, so the voluntary row is the
**only** attribute row in the LP — every attribute-price change is the mechanism's own, and
D-6 is moot; the largest DC block (`mid` 37 GW by 2030, `constants.py:2867-2874`), so the
DC-linked half is largest where the mechanism claims to matter. Rule 29's screen-year rule is
satisfied for the same reason: the year is chosen where the mechanism's **own footprint is
largest**, never where a residual is.

**PRECOMMIT — zero-LP phase 0 (rule 29 step 0), written before any solve:**

1. Compute `V(ERCOT, 2026)` for `mid` from the constants and the REF demand.
2. From the committed REF bundle (form 4 — the committed bundle IS the control; no control
   solve; a `G-DRIFT` audit of the solve-path files since REF's `git_sha` recorded in the
   PRECOMMIT): read `G_elig` = REF eligible generation, `D_elig` = REF eligible curtailment
   (dump), and `C_elig` = the eligible energy ceiling `Σ cf × cap`.
3. Declare the regime, which is the whole prediction:
   - **(i) `V ≤ G_elig`** — row slack, dual 0, LP byte-identical to REF. The screen **kills**
     the 2026 arm as inert-in-this-year and the T1-F leg is screened in the first year where
     `V > G_elig` (rule 29's inert-year clause; G-CTRL form 2). *This is the expected regime at
     `low` and plausibly at `mid` in 2026* — today's ERCOT voluntary market clears at $1–3.
   - **(ii) `G_elig < V ≤ G_elig + D_elig`** — the row binds by un-curtailing: dual small
     (the cost of redirecting a dumped MWh ≈ the dump penalty / negative-offer margin), thermal
     dispatch essentially unchanged, curtailment falls by `V − G_elig`. **"Curtailment falls
     before dispatch changes."**
   - **(iii) `G_elig + D_elig < V ≤ C_elig`** — the row displaces thermal; dual rises toward the
     clean-minus-dirty cost gap; CO2 falls.
   - **(iv) `V > C_elig`** — the escape fires: `ESC = V − C_elig` exactly, dual = WTP exactly
     (the KKT identity the trivial test pins).

**Structural gate — STOP only; it may kill the arm, never promote it (rule 29):**

| Check | Pass condition | Where it is read |
|---|---|---|
| Sign and cap | `0 ≤ dual ≤ WTP` (the I10 sign form, `check_forecast_invariants.py:647-671`) | the new `voluntary_attribute_price` in the ledger |
| Escape identity | `ESC_MWh = max(0, V − eligible generation)` and `ESC > 0 ⇔ dual = WTP` | LP result |
| Regime as predicted | the arm lands in the pre-declared regime (i)–(iv) | phase-0 numbers vs solve |
| Footprint confined | Δ-generation nonzero only on eligible columns, thermal columns and dump; storage/flows move only as a consequence of those | class-hourly sidecars |
| Direction | eligible generation ≥ REF; curtailment ≤ REF; CO2 ≤ REF (a `check_p1`-style paired monotone, `:899-911`); thermal is the only displaced footprint | `emissions_mt` (`results/export.py:200`) until WS-0's grain lands |
| No collateral flip | I1–I14 no-FAIL on the arm where REF passed | invariants |
| Control byte-identity | REF unchanged against the committed REF (form 4) | cache key + `run_config.json` |

The gate is never "did the price residual move" and never "did entry look better".

**T1-F reading (the deployment half).** In `VOL-MID`/`VOL-HI` vs REF: the entry ledger's
`attribute_price` (`new_entry.py:1565`) carries the voluntary dual in the years it binds; wind/
solar entry ≥ REF; retirements unchanged or later. **Caveat carried verbatim from plan §4:**
ERCOT's deployment half is measured-defective (R1: solar entry 0 GW vs 25.08 in hindcast;
I7/I12/I3), so the T1-F delta is a delta between two runs that share the defect —
directionally informative, never a GW forecast. The synthesis memo grades it by ERCOT's live FC
map.

**Registration and matrix.** Both legs to the forecast namespace via
`scripts/register_forecast_run.py` — `--kind scenario` once WS-0 adds it (today's choices
`t1f/ces-poc/adequacy`, `:1003-1007`) — never the backcast registry. SCN-WS3c re-stamps the ERCOT
cell (`O` → `K`/`R`/`I` with `ev`) in its own session; every other ISO stays `U` (rule 25).

**Trivial-first tests SCN-WS3b owes before any of this** (CLAUDE.md testing pattern, the
`tests/unit/policy/test_rps.py` / `test_clean_tiers.py` pattern): 1 gen / 1 zone / 24 h — (a)
binding row: dual = `mc_clean − mc_dirty` to the cent; (b) ceiling: dual = WTP, `ESC = shortfall`;
(c) `off` ⇒ LP byte-identical (row count, `n_rec_acp`, cache key); (d) coexistence with a K-row
RPS family under both netting readings; (e) the end-anchored dual offsets with all four families
present.

---

## 7. Decision boxes for the owner

Each in five lines: question, recommendation, what it blocks, the rule it touches, desk card.
Boxes M-1, M-3 and M-5 are the desk's PRESENTED cards D-3, D-6 and the voluntary part of D-2
under other names; M-2 is the plan's D-3b; M-4, M-6, M-7, M-8 are new and need desk numbering.

**M-1 — Admissibility of the axis.**
*Question:* Is a voluntary clean-demand **scenario axis** admissible, given `ffr-5b` §1.4's
inadmissibility ruling on corporate-PPA demand as a **driver**?
*Recommendation:* **Yes** — declared, forecast-only, coerced off in backcast and hindcast,
publicly anchored, levels the owner's, ledgered "Owner", never fit (§1). The `ffr-5b` null
stays disclosed for the calibrated model.
*Blocks:* everything — SCN-WS3b cannot be issued without it.
*Rule:* 13 `[R-MEASURED]`, 20 `[R-DOF]`, 24 `[R-REGISTRY]`, 22 (forecast runs unrestricted).
*Desk card:* **D-3** (PRESENTED).

**M-2 — Hourly (24/7) matching.**
*Question:* Is in-LP hourly matching built, or does 24/7 stay in the isolated portfolio tool?
*Recommendation:* **Tool** — feed it each scenario's hourly LMPs; the annual row carries the
deployment signal; an in-LP T-row block changes the LP's shape and is a portfolio problem (§2.2).
*Blocks:* nothing now; a later charter if reversed.
*Rule:* 19 `[R-ONE-MECH]`, 2 `[R-VECTOR]`; the `docs/scope2-lce-portfolio.md` isolation boundary.
*Desk card:* **D-3b** (inside D-3).

**M-3 — Netting rule against the CES target row and state RPS rows.**
*Question:* Does a voluntary MWh count toward the standard, or is the voluntary volume
additional to it?
*Recommendation:* **`additional`** as the default (one certificate market, two escapes, the
cheaper — the voluntary buyer's — fires first), field expresses both, campaign reports
`CES-P20+VOL-HI` both ways. The plan's "counts toward" reading is flagged as inverting the
retirement fact (§4.2).
*Blocks:* the `CES-P20+VOL-HI` / `ALL-CLEAN` cases only — **not** the ERCOT build or probe.
*Rule:* 19 `[R-ONE-MECH]`, 1 `[R-STRUCT]`; plan §4 "attribute double-claiming".
*Desk card:* **D-6** (PRESENTED).

**M-4 — Eligible set.**
*Question:* Renewable-only (`wind, solar, geothermal, offshore_wind`) or carbon-free
(+ `nuclear`, `gas_cc_ccs`)? And is voluntary value credited to new builds only (additionality)?
*Recommendation:* **Renewable-only default**, carbon-free as a second path label; **no**
additionality restriction at the retirement screen (§4.1).
*Blocks:* the default of `voluntary_eligible_fuels`; WS-3b can build with the default and
carry the alternative as a label.
*Rule:* 14 `[R-ACCURATE]` (the SOURCED volume anchor is a renewable definition), 19.
*Desk card:* **NEW** — desk to number.

**M-5 — Levels.**
*Question:* The `s_base` knots, `f_commit` fractions and the WTP ladder per path (§3.4's
illustrative table).
*Recommendation:* Take §3.4 as the illustrative default; the WTP `mid` point is the cell most
needing an owner number; every level is arithmetic from a SOURCED anchor with its assumption
stated.
*Blocks:* the constants SCN-WS3b writes; the build can land on the illustrative levels labelled
as such, exactly as WS-2a's prompt does for the CES target.
*Rule:* 5 `[R-NO-MAGIC]`, 24; plan §6 D-2 ("scenario levels are the owner's what-ifs").
*Desk card:* **D-2** (PRESENTED), voluntary column.

**M-6 — Allocation key intake.**
*Question:* Intake EIA-861 commercial/industrial retail sales by ISO for the non-DC allocation
(no `eia-861` datatype exists), or run on the uniform national share?
*Recommendation:* **Uniform national share now** (zero intake, reproducible), EIA-861 later
only if a scenario result is sensitive to it — the D-4 posture ("I'm not getting more data").
Procurement-location allocation disclosed, not used (§3.3).
*Blocks:* nothing; the build ships the uniform key.
*Rule:* 13, 14, 25 `[R-ISO-SCOPE]`.
*Desk card:* **NEW** — or folded into **D-4**.

**M-7 — Field budget (desk, not owner).**
*Question:* The plan budgets ≤ 3 fields; "report both" on D-6 needs a fourth
(`voluntary_netting`). Amend the WS-3 budget to 4, or fold the netting into the path grammar?
*Recommendation:* **Four fields** — a netting choice hidden in a path label is an off-registry
knob in spirit.
*Blocks:* SCN-WS3b's field list.
*Rule:* 24 `[R-REGISTRY]`, 28 (one row covers all four — sub-scalars of one family).
*Desk card:* **NEW (desk-level)** — a plan §3 WS-3 text edit, no owner needed unless the desk
says so.

**M-8 — Zone grain (deferred).**
*Question:* Should the voluntary row ever be per-zone (a DC-zone-matched buyer region on the
K-row mask) rather than ISO-wide?
*Recommendation:* **Defer** — ISO-wide is arithmetically exact under free intra-ISO REC trade
(the FFR-6B §2.1 finding that makes every non-MISO RPS row ISO-wide); a per-zone grain is a
data change to the mask if ever wanted.
*Blocks:* nothing.
*Rule:* 19, 2.
*Desk card:* **NEW** — record only.

---

## 8. Scope attestation and what this memo did NOT do

- **No code, no solve, no default, no field, no constant, no test, no matrix cell, no
  dashboard touch, no scorecard move.** The only file created or modified is this one. The plan
  §5.1 and ledger §3 **Voluntary column is UNMOVED** — a memo proves nothing, and the column
  says `no` / `—` in every row until SCN-WS3b (rows 1/2/4/5) and SCN-WS3c (rows 3/7) land.
- **No ruling assumed.** D-3 and D-6 are argued (§1, §4.2), not decided; the recommendations
  are labelled as such.
- **No solve was wanted.** Every place a number would have needed an LP is a box in §7 instead
  (the PRECOMMIT rule of the charter).
- **Rule 28 discharge:** no cell moved, no row minted; the `voluntary_clean_demand` row is
  minted by the PR that creates the field (duty 28(c)), recorded in §5 so the duty is not lost.
- **Rule 24 discharge:** nothing landed; §5 names the *entire* prospective surface (three
  fields, a fourth under M-7) so a later implementation cannot widen it invisibly.
- **Rule 22 held:** no out-of-training year solved, scored or intaken; every anchor is a
  forward-looking public document or a public statistic of 2023 — no H1-2026 actual anywhere.
- **Rule 25 held:** no ISO's fitted value crosses a boundary; the national anchors are shared
  public data allocated by a public key.
- **What was not verified:** the NREL product breakdown and state tables (PDF unreachable
  through the proxy), the LBNL hyperscale share, the Green-e double-claiming clause and the
  CEBA state ranking — each marked `NEEDS-CITATION` and each ships as 0 / disclosed until read.

---

## Routing note (for SCN-DESK)

**Boxes the desk must present to the owner:** **M-1 (= D-3)** and **M-3 (= D-6)** are already
PRESENTED — this memo is their brief; **M-5** is the voluntary column of the PRESENTED **D-2**;
**M-2 (D-3b)** rides inside D-3; **M-4** (eligible set) and **M-6** (allocation intake, or fold
into D-4) are NEW cards for the desk to number. **M-7** (field budget: 3 → 4) is a desk-level
plan §3 WS-3 text edit, not an owner ruling; **M-8** is record-only. **What SCN-WS3b consumes
once M-1 is signed:** §2.1 (Option A on the shared row family, after WS-2a's coupling
relaxation — which did not exist as a branch at this lane's start and is an assumed
precondition), §3.1/§3.3 (the resolver and the uniform allocation), §3.4 (illustrative levels
until D-2), §4.1's default eligible set, §5 entire (fields, coercion, cache registries,
`TIER_TAGS`, matrix row + six cells as the last commit), and §6's trivial-first tests; M-3
(D-6) gates only the `voluntary_netting` semantics and may land after the build with the
`additional` default. **What SCN-WS3c consumes:** §6 entire (PRECOMMIT regimes, structural
gate, T1-F reading, `PAIRED_ARM_OVERRIDES` arms, registration kind). **Files outside this
lane's region touched: none;** the memo describes `policy/voluntary_demand.py`,
`model/lp/rows.py`, `model/lp/model.py`, `data/datacenter.py`, `config/scenarios.py` and
`config/constants.py` and edits none of them (rows.py is SCN-WS2a's this wave; the rest are
SCN-WS3b's behind D-3). Nothing to STOP on.
