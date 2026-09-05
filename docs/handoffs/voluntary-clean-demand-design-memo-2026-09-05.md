# Voluntary clean-energy demand — design memo (SCN-WS3a, 2026-09-05)

**Lane:** SCN-WS3a `[FABLE]`, plan §3 WS-3 item 1 / §7 "WS-3a"
(`docs/handoffs/forecast-scenario-readiness-plan-2026-09.md`, "the plan"). Issued by the
Scenario Readiness Desk r#1 (`docs/handoffs/scenario-desk-ledger-2026-09.md`, "the ledger").
**Memo-first, the FF-0C / FF-G4 pattern: no code, no config, no test, no solve, no default, no
matrix cell.** This file is the lane's only artifact. The implementing lane (SCN-WS3b) is
chartered from §7's signed boxes and builds nothing this memo has not written down.

**Head at start:** `origin/main` `5cc1e7ce` (PR #4853, the desk charter merge — one commit past
the desk pin `d01ab8b0`; the delta is the ledger itself and touches no file cited below). Every
`file:line` below was read at this head. **SCN-WS2a's branch does not exist on the remote at
this head** (`git ls-remote origin 'refs/heads/claude/scn-*'` returns nothing), so §2 is written
against `model/lp/rows.py` and `model/lp/model.py` **as they stand**, and the relaxation of the
"clean rows require the RPS region family" coupling (`rows.py:1872-1878`, `model.py:385-390`)
is an **assumed precondition** that WS-2a delivers — stated as such wherever §2 leans on it.

**Two standing notes from the desk, written in rather than resolved:** card **D-3** (is the axis
admissible at all) and card **D-6** (netting against a federal CES) are PRESENTED and OPEN. §1 is
the brief the owner rules D-3 on; §4 is the brief for D-6. Neither ruling is assumed anywhere
in this memo, and every box SCN-WS3b needs signed before it can build is marked in §7.

---

## 0. Bottom line

**Recommend the owner rule D-3 YES — a declared, forecast-only, publicly-anchored voluntary
clean-demand axis is a different admissibility class from the corporate-PPA *driver* ffr-5b
refused, and the refusal's own four sentences, read one at a time, do not reach it (§1).** The
ffr-5b null stays exactly where it is: the reference case carries no voluntary demand, the
hindcast and crossover lanes carry none, no rubric score moves, and no keeper's DOF ledger gains
an entry. What the axis adds is a **what-if over the null**, in the same class as
`carbon_price_path` and `datacenter_load_path`.

**Representation (§2): one annual volumetric clean-attribute row per ISO-year with a
willingness-to-pay escape**, built as **one more region of the existing clean-tier row family**
(`rows.py:205-293`) with an all-zone eligibility mask, a volume RHS expressed through the
builder's own obligation-fraction algebra (`rows.py:292`), and its escape column priced at the
buyer's WTP ceiling instead of a statutory ACP (`layout.py:71-84`, `costs.py:255-261`). Its dual
is the voluntary REC / PPA attribute price and reaches entry and retirement through the
**existing** `max()` seam (`new_entry.py:1118-1128`, `retirements.py:3178-3183`) — one
certificate, sold once, no new consumer. The hourly-matched (24/7) variant is **deferred** with
its two reasons written out (§2.2); the entry-screen-only price adder is **rejected** because it
has no dispatch footprint and already exists as the `eac_price_*` scalars (§2.3).

**Volume (§3): DC-linked.** `V(ISO, y) = s_base(ISO) × E_nonDC(ISO, y) + f_commit(y) ×
E_DC(ISO, y)`, where `E_DC` is the energy of the data-center block the model already builds
(`data/datacenter.py:211-236`) — so a high-DC case and a high-voluntary case are coherent by
construction. The anchors are public (NREL's voluntary-market status report, the hyperscalers'
published commitments, EIA-861 commercial retail sales for allocation); §3.3 says cell by cell
which are sourced in-repo today and which are `needs-citation`. **No anchor is proprietary and
none is a number this memo invents** — the two cells with no public level (the committed share
of DC load; the WTP ceiling) are owner levels under D-2, exactly as every other scenario level.

**Eligibility (§4):** wind / solar / offshore wind / geothermal by default (the voluntary
renewable market's set); nuclear and CCS for "carbon-free" programs are **owner box D-3c**.
**Netting (§4.3, card D-6):** only has content against WS-2a's CES *target* row (under the
premium ladder there is no federal row to net against, and the `max()` composition already
answers the price question); recommend **counts-toward** as the default dispatch posture (two
independent rows — the FFR-6B §6.4 doctrine, zero code) with **additional** as the campaign's
second reported posture, and the reason certificate mechanics could argue the other way is
stated rather than buried.

**Fields (§5): three plus one.** `voluntary_clean_demand_path` (`"off"` default, coerced
`"off"` in backcast/hindcast — the `datacenter_load_path` pattern, `scenarios.py:15739-15746`),
`voluntary_wtp_ceiling_usd_per_mwh` (`None` = the cited constant), `voluntary_eligible_fuels`
(`None` = the cited default set), all cache-optional at their inert defaults so every backcast
and forecast key is byte-stable; plus the D-6 posture switch, which is a fourth field the
plan's "≤ 3" budget did not foresee and is routed to the desk (§8).

**Probe (§6):** ERCOT 2026 T0, REF vs `mid`, a zero-LP phase 0 first, a structural STOP-only
gate, the committed REF bundle as control. **The plan §5.1 Voluntary column is left UNMOVED by
this memo — a memo proves nothing.**

---

## 1. The ffr-5b ruling, line by line — why a declared scenario axis is a different admissibility class (card D-3)

### 1.1 What the ruling was about

`docs/handoffs/ffr-5b-procurement-channel-design-2026-08-05.md` §1.4 (lines 226-243) adjudicated
**Candidate D — corporate PPA demand — as a *driver of VRE entry*** inside the capacity-evolution
loop: a quantity the model would carry in its default posture, whose value would have to be
*identified* from data, and whose correctness the model's forecast skill would then depend on.
The ruling's frame is stated at its top (`:70-71`): rule 13's test verbatim, *"could this same
quantity be produced for a forward year from forward drivers, and would it respond to changed
conditions?"*, sharpened by the instrument test and the horizon test (`:75-80`). The verdict at
`:243` and the disposition at §5.4 (`:560-572`) are: **inadmissible as a channel; the honest
deliverable is a disclosed limitation with a named size.**

This memo does **not** reopen that. The reference case (plan §3.0: `policy_bundle="current"`,
`datacenter_load_path="mid"`, `federal_ces_enabled=False`), every T1-H / T1-X hindcast, every
FF-2D rubric verdict and every backcast keeper keep the ffr-5b null. What is proposed is an
**explicitly-labelled, default-off, forecast-only scenario arm** whose whole purpose is to be
moved — the same class as `carbon_price_path` (RFF paths), `datacenter_load_path`
(`scenarios.py:2843-2859`, ISO queue reports) and `electrification_path`
(`scenarios.py:2872-2894`). The plan's §2.3 (`:258-265`) already draws this line; §1.2 below is
the argument for it, sentence by sentence against the ruling.

### 1.2 The four sentences of §1.4, and what each does and does not reach

**Sentence 1 — "What identifies it. Nothing admissible. The usable volume series (BNEF, LevelTen
PPA Price Index, S&P) are proprietary — they cannot enter `data/raw/` as a re-queryable source and
a future session cannot reproduce them at a vintage, which fails rule 13's reproducibility clause
before the forward clause is even reached."** (`:228-231`)

*Agreed, and preserved.* No proprietary series enters this design at any point — §3.3's anchor
table has no BNEF, LevelTen or S&P cell, and a build that reached for one would fail this memo's
own §5 guard. But the sentence is about **identification**: a driver must be *identified* from a
series, so the series' reproducibility is the driver's reproducibility. A scenario axis is not
identified from anything. Its **level** is declared, and what rule 13's reproducibility clause
asks of a declared level is exactly what it asks of `DATACENTER_ADDITIONS_MW`
(`constants.py:2858-2871`: *"parameters.json tier 2, modeled flag OFF (a forward input, not a
fitted knob)"*) — that the number sit in `constants.py` with a citation to a **public** document
so that any third party regenerates the identical run from the committed config. §3.3's anchors
are public documents (an annual NREL report, corporate sustainability filings, an EIA form), so
the clause is **satisfied, not evaded**. The test rule 13 actually states is whether the quantity
is *"a measured outcome fed back in"*; a scenario level is neither measured nor an outcome.

**Sentence 2 — "CEBA's public deal tracker is announcement-grade, deal-count-oriented and not
resolved to ISO or to an EIA plant identity."** (`:231-232`)

*Agreed as a statement about the tracker; irrelevant to the axis, for three reasons.*
(i) "Announcement-grade" is disqualifying for a driver and is precisely the grade a **what-if
level** is allowed to be — the plan's D-2 row (`:779`) says it: *"Scenario levels are the
owner's what-ifs by definition; never a modeller's tuning."* (ii) ISO resolution is supplied by
an **allocation rule** (§3.2), the same way the RPS compliance regions allocate a state statute
onto model zones from EIA-861 retail sales (`capacity_market.py:4588-4594`) — a disclosed
arithmetic, not an identification. (iii) Plant identity is irrelevant because the row is a
**zone-aggregate attribute constraint with no vintage**: the LP's wind and solar columns are
`W[z,t]` / `S[z,t]` per zone (`rows.py:76-77`), with no plant identity to match a PPA to. Annual
REC matching in the real voluntary market has no plant identity either. §3.3 uses CEBA only as
trend context, never as a level, and says so.

**Sentence 3 — "Forward analogue. None exists. No published forward corporate-procurement volume
series exists at ISO grain, so a forward number would be a modeller's assumption — a free
parameter, refused by rule 20 `[R-DOF]` (…) and by rule 24 the moment it needed a
`ScenarioConfig` home."** (`:234-237`)

*This is the sentence D-3 turns on, and it conflates two things.* Rule 20's text is: *"A
residual that can only be closed by a tuned value is an open root-cause issue, not a
parameter."* A **DOF** is a value identified **against a residual** — the DOF ledger exists to
list every free parameter *with its identification source*. A scenario level has no
identification source because it is never identified: it is set by the owner (D-2), it is
`"off"` in every reference and every scored run, and it is **coerced inert in backcast** (§5.2),
so it cannot enter any keeper, cannot move any scored criterion, and cannot appear on any
keeper's DOF ledger. It closes no residual because it is present in no run that has one. The
same sentence, applied to `carbon_price_path`, would refuse the RFF paths — a forward carbon
price is likewise *"a modeller's assumption"* with no measured forward series — and the repo has
not read rule 20 that way for any scenario axis it ships.

The rule-24 half inverts the rule. Rule 24 `[R-REGISTRY]` forbids **off-registry** tuning
channels — env-var knobs, hardcoded dicts, `getattr` fallbacks. A `ScenarioConfig` field with a
citation, visible in `run_config.json`, *is* the registry. The field's home is what makes the
axis auditable, not what makes it a parameter.

What sentence 3 gets right, and this memo keeps: **the level is an assumption.** The design's
job is to make the assumption's anchor public, its arithmetic disclosed (§3.1), its ISO
allocation reproducible (§3.2), and its two genuinely un-anchored cells (§3.3 rows 8 and 12)
owner-set under D-2 with that status printed next to them.

**Sentence 4 — "And its realized half is already inside Candidate A: a corporate PPA that is
actually signed produces an interconnection agreement and a proposed-generator row. So the
channel does not lose the phenomenon — it loses only the *unsigned* part, which is the part
nobody can observe."** (`:239-241`)

*Agreed, and the design honours it in both halves of the model.* In **dispatch**, the row is an
attribute constraint over existing and entering eligible columns; a plant that entered through
the FFR-5E procured channel (`procured_vre_additions`, `runner.py:4500`) sits in the same
`W`/`S` columns and satisfies the voluntary row like any other eligible MWh — no MWh is counted
twice because the row counts generation, not contracts. In **capacity evolution**, the procured
channel is a *quantity* channel keyed to the EIA-860 queue and the voluntary row is a *price*
signal to the merchant screen; the two compose exactly as the RPS dual already composes with
that channel today (`rows.py:232-234`, E-1 never acquires a build limb), so the rule-19 stacking
ffr-5b §2.3 fenced is not re-opened. The **unsigned part** is exactly what a *scenario* is
entitled to posit and a *driver* is not: the axis asks *"what if buyers procure V MWh of clean
attributes in ISO X in year y"*, it does not claim to know that they will.

### 1.3 Why this cannot become a backdoor (the guards, all existing)

1. **Forecast-only coercion.** `mode="backcast"` or `hindcast=True` coerces the path to `"off"`
   at the config seam (§5.2; the `datacenter_load_path` construction, `scenarios.py:15739-15746`,
   with the standalone `validate_*` defense in depth, `datacenter.py:323`). No scored backcast,
   no T1-H hindcast, no T1-X crossover can carry it.
2. **REF is `"off"`.** The plan's reference posture (§3.0) does not name the axis, so every T1-F
   rubric verdict, every FF-2D gate, and every §2.1b readiness reading is unchanged by its
   existence; the axis lives only in `VOL-*` arms and the `ALL-CLEAN` corner (plan §3.5 `:686`,
   `:690`).
3. **Rule 29's screen gate is structural and STOP-only.** §6's gate never reads a residual, so
   the level cannot be selected on fit even inside a forecast probe.
4. **Rule 25.** Anchors are per-ISO; the allocation rule (§3.2) is the same arithmetic in every
   ISO with each ISO's own published shares; no fitted value crosses an ISO boundary because
   there is no fitted value.
5. **D-2 sets levels, the modeller never does.** The `low/mid/high` pairs land in `constants.py`
   with citations; a session that changed a level to make a scenario "look right" would be
   violating rule 1 `[R-STRUCT]` on its face, and the matrix cell (§5.5) records what was tested.

### 1.4 The distinction in one table

| | ffr-5b's Candidate D (a *driver*) | This memo's axis |
|---|---|---|
| Lives in REF / BAU | yes — it would move the default forecast | **no** — `"off"` |
| Enters hindcast / crossover scoring | yes — forecast skill depends on it | **no** — coerced off |
| Identified against data | must be (a residual-closing quantity) | **never** — declared level |
| Rule 13 reproducibility | fails (proprietary series) | satisfied (public anchor + cited constant) |
| Rule 20 DOF | a free parameter in a scored model | absent from every scored model |
| Rule 24 | needs an off-registry home or none | the registry *is* the home |
| Responds to changed conditions | must, endogenously | **is** the changed condition |
| Precedent | — | `carbon_price_path`, `datacenter_load_path`, `electrification_path` |

**Owner box D-3 (§7): YES / NO.** If NO, the plan's `VOL-*` and `CES-P20+VOL-HI` cases drop with
a ledger note (ledger §1, SCN-WS5A row) and this memo is the record of why the class distinction
was not accepted.

---

## 2. Representation options — each against rules 1, 2 and 19

### 2.0 What already pays a clean MWh (the rule-19 enumeration, done first)

Before any new mechanism, the D-2-style enumeration of everything that already floors or pays
the phenomenon:

| channel | where | dispatch footprint | screen footprint | kind |
|---|---|---|---|---|
| legacy `eac_price_*` scalars (wind, solar, nuclear, CCS, offshore, geothermal, storage) | `scenarios.py:3063-3074`; `eac.py:39-47` | yes — subtracted from `mc` / added to `wind_mc`, `solar_mc` (`eac.py:50-115`, `:118-165`) | yes — via `effective_eac_price_for_tech` (`new_entry.py:1119`) | exogenous **price** |
| federal CES premium | `scenarios.py:3084-3157`; `federal_ces.py:63-123`, `:523-559` | yes — same two entry points, `max(legacy, premium × credit)` | yes — same `max()` | exogenous **price** |
| state RPS row (single or K-row) | `rows.py:27-95`, `:205-293`; armed `runner.py:2851-2864` | yes — a constraint row; dual = REC price | yes — `rps_credit_for_zone` (`new_entry.py:1120`, `retirements.py:3161-3165`) | endogenous **quantity → price** |
| state clean-tier rows (MISO) | `clean_tiers.py:89-140`; `rows.py:1851-1871` | yes — constraint rows; dual = clean attribute price | yes — `clean_credit_for_zone` (`new_entry.py:1121-1127`, `retirements.py:3178-3183`) | endogenous **quantity → price** |
| §45U nuclear PTC | `retirements.py:3186+` | no | yes — composes with the `max()` winner, not inside it | tax credit, separate instrument |

Composition doctrine, already in force and untouched here: in **dispatch** the rows are
independent constraints and one MWh may satisfy several of them (`rows.py:1846-1850`, FFR-6B
§6.4); at the **screens** the credit is `max()` across attribute buyers, never a sum
(`eac.py:10-21`; `new_entry.py:1118-1128`; `retirements.py:3181-3183`). A voluntary buyer is one
more attribute buyer. It therefore must enter as a **row** (its phenomenon is a *quantity* of
attributes demanded at a price ceiling) whose dual joins that `max()` — and must **not** enter
as a second price on top of the `eac_price_*` channel, which would be the exact stacking rule 19
forbids and §2.3 rejects.

### 2.1 Option A — annual volumetric attribute row with a willingness-to-pay escape (RECOMMENDED)

**The row.** One annual inequality per ISO-year:

```
Σ_t Σ_{z ∈ all zones} ( W[z,t] + S[z,t] )
  + Σ_t Σ_{g ∈ eligible non-W/S classes} P[g,t]
  + Σ_t ESC_vol[t]                                   ≥  V(ISO, y)   [MWh]
```

with `ESC_vol[t] ≥ 0` priced at the WTP ceiling `w` in the objective. The dual is the voluntary
attribute price: `0` when the row is slack, in `(0, w]` when binding, exactly `w` when the
escape fires (the buyer stops buying at its ceiling and the shortfall is the un-procured
volume). This is the RPS row's form (`rows.py:33-48`) with three differences the plan names
(`:554-560`): the RHS is a **volume**, not a share of load; eligibility is the voluntary
market's; the escape is a **willingness to pay**, not a statutory ACP.

**Where it lives — one more region of the clean-tier family.** The K-row builder
`_build_rps_region_rows` (`rows.py:205-293`) already does everything the row needs:

- an eligibility mask per region over the wind/solar zone columns (`:270-272`) — the voluntary
  region's mask is all-`True` (any zone's certificate serves any buyer in the ISO; the same
  free-intra-ISO-trade premise FFR-6B §2.1 uses for the single ISO-wide RPS row);
- optional non-W/S generator columns resolved per region through
  `_resolve_clean_region_gen_idx` (`rows.py:145-202`, `:274-278`) — geothermal today, nuclear
  and CCS if D-3c admits them (this resolver admits nuclear, `:153`; the renewable resolver
  refuses it by name, `:128-133`, so the voluntary row must ride the *clean* family, not the
  renewable one, the moment nuclear is on the table);
- a per-region ACP escape column, one non-negative variable per hour (`layout.py:71-84`,
  `rows.py:279-281`), with its own price in the objective (`costs.py:255-261`, a `(n_rec_acp,)`
  vector — the WTP lands there as the voluntary region's entry) and an infinite upper bound
  (`bounds.py:287-289`);
- a vectorized build — the only Python loop is over `K ≤ 6` regions, never hours
  (`rows.py:269`; rule 2 `[R-VECTOR]` satisfied by construction).

**The volume RHS through the builder's own algebra.** The builder computes
`rhs = obligation_frac @ zone_annual_demand` (`rows.py:292`). A volume `V` is expressed
**without touching the builder**: the resolver (`policy/voluntary_demand.py`, §5.1) allocates
`V` across zones by weights `ω_z` (§3.2) and sets `frac[z] = V·ω_z / D_z` for every zone with
`D_z > 0` (ERCOT `Panhandle` carries `load_share = 0.0`, `iso_configs.py:194`, and receives
`ω = 0`), so `Σ_z frac[z]·D_z = V` identically. The volume-to-fraction step is the resolver's,
the row builder stays a pure column-append, and the K=1/all-zones byte-identity the family
already proves (`tests/unit/model/test_dispatch.py:1180-1193`) is the regression anchor.

**Dual plumbing, zero new consumer.** `clean_credit_by_fuel` (`clean_tiers.py:143-174`) maps
region duals to `{fuel: (n_zones,)}` credits by taking the **max over admitting regions per
fuel per zone** (`:170-173`); a voluntary region with an all-zone mask and its eligible fuels is
one more admitting region, so the voluntary dual composes with the state clean duals inside the
same dict. That dict is `PriorYearResults.clean_attribute_price_by_fuel`
(`runner.py:4514-4521`), read by both screens through `clean_credit_for_zone`
(`new_entry.py:1121-1127`, `retirements.py:3178-3180`) inside the attribute `max()`. The dual
reaches entry and retirement with **no new argument, no new seam**.

**Against rule 1 `[R-STRUCT]`.** This is how the voluntary market clears: annual matching of
certificates (bundled PPA RECs, unbundled RECs, green tariffs) against a buyer's annual
consumption, at a price the buyer is willing to pay and above which it does not buy. The dual
*is* the voluntary REC price; the escape *is* the buyer's ceiling. In dispatch the row's binding
pulls curtailed clean MWh out of the dump columns first (a REC buyer's first purchase is the
cheapest attribute, and a dumped MWh's certificate costs the system nothing) and then displaces
thermal — the observable that plan §3 WS-3 item 3 names as the probe's ordering gate.

**Against rule 2.** Builder vectorized (above); one row per ISO-year, so LP size is unchanged
beyond `T` escape columns (`n_rec_acp += 1`, `model.py:402` pattern).

**Against rule 19.** One row family for "a buyer demands a quantity of clean attributes at a
price ceiling"; the RPS, clean-tier and (WS-2a's) federal CES-target rows are the same family's
other regions, and the screens' `max()` already refuses to stack their duals. No adder, no
second price, no build limb (the row's only output is a price — `rows.py:232-234` applies).

**What the assembler cannot do today — the assumed precondition.** The clean family is
admitted only when the per-region RPS family is on (`rows.py:1872-1878`: *"clean_region_zone_mask
(clean-tier rows) requires the per-region RPS family"*; enforced again at layout time,
`model.py:385-390`), and the family is built only for MISO (`clean_tiers.py:115-116`, gated in
the runner by `miso_clean_tier_rows` inside `_rps_region_grain_active`, `runner.py:2855-2860`).
SCN-WS2a's charter (plan §7 "WS-2a" item 1, `:897-899`) relaxes exactly this coupling so a
**federal region spanning every load zone** can stand alone or beside the state rows. This memo
assumes that relaxation lands in the shape *"the clean family may be non-empty when the RPS
region family is empty, and its ACP slots are counted from `acp_k0 = K1` whatever K1 is"* — the
slot arithmetic at `model.py:371-402` and the end-anchored dual read at `model.py:1196-1219`
both already count the clean family by its own length, so a third region in it needs no new
anchor. **If WS-2a lands a different seam, §2.1's "one more region" construction is re-pointed
at whatever WS-2a built, and the desk is told (§8).** The recommendation to the desk is that
WS-2a's federal row and WS-3b's voluntary row use the *same* construction — extra regions of the
one family — so the relaxation is written once.

**What stays open in Option A (named, not hidden).**
- *No additionality mask in dispatch.* The LP's `W`/`S` columns are zone aggregates with no
  vintage (`rows.py:76-77`), and annual REC matching has none either. If the owner wants
  voluntary value credited to **new builds only**, that is an **entry-screen rule** (credit the
  voluntary dual in `new_entry` and not in `retirements`), never a dispatch mask — flagged in
  D-3c's fifth line, not designed here.
- *Deliverability.* An all-zone mask lets a Panhandle wind MWh serve a Houston buyer's annual
  claim; that is the voluntary market's actual convention (RECs are not deliverability-tested)
  and the same premise the ISO-wide RPS row already carries.

### 2.2 Option B — hourly-matched (24/7) T-row block (DEFERRED; owner box D-3b)

**The form.** Per buyer `b` and hour `t`:
`Σ_{z ∈ zones(b)} (W[z,t] + S[z,t] + eligible P) ≥ L_b[t] − ESC_b[t]`, i.e. `T` rows and `T`
escape columns per buyer, buildable vectorized with `sp.kron(eye(T), ·)`. Feasible under rule 2.
Deferred for two reasons the plan names (`:582-586`) and this memo makes concrete:

1. **LP shape.** Every existing mechanism appends to a fixed per-hour column block
   (`layout.py`, `vars_per_hour`); a per-buyer hourly escape adds `T × n_buyers` columns and
   rows and moves every downstream offset the layout's own comments promise to keep unchanged
   (`layout.py:66-69`, `:80-83`). Option A adds one row and rides an existing column class.
2. **The portfolio problem.** An hourly-matched buyer chooses *which* resources and *how much
   storage* to contract — a resource-selection problem. Giving the market LP that choice means
   giving each buyer its own contract and storage decision variables, which is a different
   optimization from market dispatch. The repo already has that optimization, deliberately
   isolated: `scope2-lce-portfolio/` selects a clean + storage portfolio to match an 8760 load
   hour-by-hour at the lowest premium above wholesale, consuming the simulator's LMPs as a file
   and importing nothing from `market_sim` (`docs/scope2-lce-portfolio.md:7-15`, `:26-33`).
   Feeding it the `VOL-*` scenario LMPs answers the 24/7 question **without** contaminating the
   dispatch LP — which is the stated reason the tool is separate (`:38-41`).

A third reason, structural: with zone-aggregate `W`/`S` columns and no contract identity, an
in-LP "matched" MWh is indistinguishable from the system's hourly clean share in that zone — a
reporting quantity, not a constraint a buyer can satisfy. **Recommendation:** 24/7 stays in the
tool; reserve an in-LP hourly row for a later owner box (D-3b) and record the deferral rather
than leaving it implicit.

### 2.3 Option C — entry-screen-only price adder (REJECTED)

An exogenous voluntary attribute price added inside `effective_eac_price_for_tech` or as a new
`eac_price_*` scalar. Rejected on three grounds:

- **Rule 1 — no dispatch footprint.** No row, no dual, no curtailment response; the
  voluntary buyer's observable is its **volume**, and a price-only representation makes that
  volume an output nobody checks against the anchor.
- **Rule 19 — it already exists.** `eac_price_wind` / `eac_price_solar`
  (`scenarios.py:3064-3065`) already reach dispatch through the `wind_mc` / `solar_mc` adders
  (`eac.py:118-165`) and the screens through the same `max()`; if an exogenous voluntary
  *price* were what the owner wanted, the mechanism is those scalars with a year path, not a
  new one.
- **It cannot express the ceiling.** A buyer that stops buying at `w` is a quantity phenomenon
  with a price cap; an adder has no quantity to stop at.

---

## 3. The DC-linked volume construction and its public anchors

### 3.1 The construction

```
V(ISO, y) = s_base(ISO, path) × E_nonDC(ISO, y)  +  f_commit(y, path) × E_DC(ISO, y)
```

- `E_DC(ISO, y) = Σ_z datacenter_block_mw_by_zone(config, ISO, y)[z] × T`
  (`data/datacenter.py:211-236`: `resolve_datacenter_mw` (`:105-151`, the low/mid/high
  `DATACENTER_ADDITIONS_MW` interpolation) × `datacenter_load_factor` (`scenarios.py:2864-2867`,
  LBNL 2024 / EPRI 2024) distributed by `datacenter_zone_shares` (`:154-160`)). The block is flat,
  so `ΔEnergy = block_mw × 8760` in closed form (`:217-219`).
- `E_nonDC(ISO, y) = Σ_{z,t} year_demand[z,t] − E_DC(ISO, y)`, read **after** the block is folded
  in (`add_load_layers` at `runner.py:1957` / `:2474`). In the relocate regime total energy is
  invariant (`datacenter.py:315-317`), in the tail regime the block is additive (`:318-320`); in
  both, `E_nonDC` is the served energy that is not the DC block.
- `s_base(ISO, path)` — the voluntary share of **non-DC** load (the pre-existing voluntary
  market: utility green pricing, unbundled RECs, CCAs, corporate PPAs outside data centers).
- `f_commit(y, path)` — the share of the DC block's energy under a **published 100 %-clean /
  carbon-free annual-matching commitment** in year `y`.

The DC half is the reason voluntary demand is growing, and riding the existing
`datacenter_load_path` block makes the two axes **coherent by construction**: a `LOAD-HI`
(`datacenter_load_path=high`) case raises `E_DC` and therefore `V` without a second knob, and a
`VOL-HI` case at `datacenter_load_path=mid` moves only the attribute demand, so the paired
comparison against REF is clean (§6). The `off` path returns `V = 0` and no row (byte-identity).

### 3.2 ISO allocation and zone allocation

- **The DC half is already at ISO and zone grain** (`DATACENTER_ADDITIONS_MW[iso]`,
  `DATACENTER_ZONE_SHARE[iso]` for ERCOT and PJM, `constants.py:3008-3041`; SCN-WS4a is adding
  the ERCOT and MISO shares this wave, ledger §4 `:172`). Nothing to allocate.
- **The non-DC baseline is national in its source** (NREL reports national volumes by
  product), so it needs an ISO allocation. Recommended weight: each ISO's share of **U.S.
  commercial-sector retail sales** from EIA-861 (state-level, public annual CSV), mapped
  state → ISO with the same hand-transcribed retail-sales basis the MISO compliance regions
  already use (`capacity_market.py:4588-4594`: *"within-zone state load shares from EIA-861 2023
  retail sales restricted to the MISO-served portion"*). Commercial sales rather than total
  sales because the voluntary market's buyers are overwhelmingly commercial customers (the
  NREL product tables split volumes by customer class — the exact split is a `needs-citation`
  cell). Within an ISO, the baseline allocates to zones by `load_share`
  (`iso_configs.py:193-199` for ERCOT), the DC half by `DATACENTER_ZONE_SHARE` where published,
  else `load_share` (the `datacenter_zone_shares` fallback, `datacenter.py:154-160`).
- **EIA-861 is not on disk.** The `data/raw` tree at this head (read with
  `GIT_NO_LAZY_FETCH=1 git ls-tree`, trees only) has no `eia-861` directory; the MISO shares
  above were transcribed from it by hand. Intaking the one state × sector sales CSV is a
  public-data intake and, per rule 22's 2026-08-06 clarification (*"Data intake needs NO
  per-ISO/per-window authorization"*), needs no box — it is routed to WS-3b's data profile
  (§8). It is **not** the paid-data class the owner's Q23 declined.

### 3.3 Per-cell provenance table

Status legend: **sourced** = the number is already in the repo with its citation;
**public / needs-citation** = a public document exists and names the number, but no session has
transcribed it into `constants.py` with a citation yet; **owner level** = no public source pins
the value, so it is a D-2 what-if level with the candidate range disclosed.

| # | cell | role in §3.1 | candidate public source | status |
|---|---|---|---|---|
| 1 | DC block MW trajectory, low/mid/high, per ISO | `E_DC` | ERCOT 2025 constraints report + LFL updates; PJM 2025 LTLF; CEC 24-IEPR-03; NYISO 2025 Gold Book; MISO 2025 LTLF (`constants.py:2858-2919`) | **sourced** |
| 2 | DC flat load factor 0.85 | `E_DC` | LBNL 2024 DC energy report; EPRI 2024 (`scenarios.py:2864-2867`) | **sourced** |
| 3 | DC zone shares (ERCOT, PJM) | zone allocation of the DC half | ERCOT 2025 Adjusted LTLF large-load additions; PJM DOM anchor (`constants.py:3008-3041`) | **sourced**; MISO/ERCOT refresh in flight (WS-4a) |
| 4 | Zone `load_share` per ISO | zone allocation of the baseline | `iso_configs.py` (ERCOT `:193-199`), `scripts/data/derive_load_shares.py` | **sourced** |
| 5 | Served energy by ISO-year | `E_nonDC` | the run's own demand (`runner.py:1957`) | **sourced** (model input) |
| 6 | National voluntary retail sales by product (PPAs, utility green pricing, unbundled RECs, CCAs, competitive suppliers), latest year | `s_base` level | NREL, *Status and Trends in the U.S. Voluntary Green Power Market* (annual; public report + data tables) | **public / needs-citation** — edition, table and year to be named in `constants.py` |
| 7 | Voluntary sales by customer class (commercial vs residential) | `s_base` allocation basis | same NREL report | **public / needs-citation** |
| 8 | Voluntary market growth path to 2030+ (low/mid/high `s_base(y)`) | `s_base` trajectory | NREL report's multi-year series for the trend; CEBA Deal Tracker public aggregate **as trend context only** (per ffr-5b sentence 2, never a level) | **owner level** — the trend is public, the forward path is a D-2 what-if |
| 9 | Commercial-sector retail sales by state (EIA-861) | ISO allocation of the baseline | EIA Form 861, Sales to Ultimate Customers (annual, public CSV) | **public / needs-intake** (not in `data/raw`) |
| 10 | State → ISO membership for the allocation | ISO allocation | the repo's existing BA/ISO basis; the MISO hand transcription precedent (`capacity_market.py:4588-4619`) | **sourced pattern** |
| 11 | Hyperscaler commitment targets and target years | `f_commit` shape | Google (24/7 carbon-free energy by 2030, 2020 announcement); Microsoft ("100/100/0" by 2030, 2021); Amazon (100 % renewable matching, reported met 2023); Meta (100 % renewable matching, reported met 2020) — each in the company's published sustainability report | **public / needs-citation** — document and page per company |
| 12 | Share of the DC block operated by committed buyers | `f_commit` level | no public ISO-resolved series (hyperscale vs colocation vs enterprise DC shares are proprietary market research) | **owner level** — recommend `low = 0`, `high = 1.0` (the whole block committed), `mid` an owner choice; **the weakest cell in the construction, said plainly** |
| 13 | Annual-matching vs 24/7 form of the commitment | eligibility, §2.2 | same corporate reports | public; only annual matching is modelled (D-3b) |
| 14 | WTP ceiling `w`, real 2026$/MWh, low/mid/high | escape price | national voluntary REC price ranges (Green-e / public market reports); the range already cited in-repo — *"national voluntary RECs $2–7/MWh"* and *"Platts Type-2 hourly certificates $0.90–5.00/MWh"* (`docs/handoffs/ces-ci-crediting-audit-2026-07.md:683-687`, from the portfolio tool's `eac_prices.csv`); bundled-PPA premia (LevelTen) are **proprietary and refused** | **public / needs-citation** for the REC range; the ceiling itself is an **owner level** (D-2) |
| 15 | Eligible fuel set | row LHS | Green-e Energy standard (renewable set; new/low-impact hydro only); the corporate "carbon-free" definitions for nuclear (row 11) | public; the **choice** is D-3c |

**Reading the table honestly.** Rows 1–5 and 10 are on disk today. Rows 6, 7, 9, 11, 14 have
public sources a build session transcribes with citations (rule 5 `[R-NO-MAGIC]`, the
`DATACENTER_ADDITIONS_MW` comment discipline). Rows 8, 12 and the level of 14 are **what-if
levels** — the memo does not pretend otherwise, and they are exactly the cells D-2 exists for.
Nothing in the table is identified against a model residual, and nothing is proprietary.

### 3.4 Interaction with the growth double-count discipline

The DC block already *relocates* rather than adds its energy at the mid path
(`constants.py:2846-2852`, `datacenter.py:260-280`). `V` reads `E_DC` and `E_nonDC` from the
served demand **after** relocation, so the same energy is never counted in both halves; the
`E_nonDC` term is the residual by definition. A `LOAD-HI` case in the tail regime (ERCOT high,
`datacenter.py:282-288`) raises `E_DC` additively and `V` follows — which is the intended
coherence (plan G-L3 names the pairing question; this construction does not add to it).

---

## 4. Eligibility, and the netting rule against a federal CES (card D-6)

### 4.1 Default eligibility — the voluntary renewable market's set

`("wind", "solar", "offshore_wind", "geothermal")`. Wind and solar are the zone columns
(`rows.py:101`); `offshore_wind` and `geothermal` are fleet fuel types (`eac.py:39-47`) that
resolve to generator columns through `FUEL_TYPE_MAP` inside `_resolve_clean_region_gen_idx`
(`rows.py:191-201`; an unknown name hard-errors, never silently drops, `:193-198`). Hydro is
**excluded by default**: the voluntary market's dominant certification standard admits only
new or low-impact hydro, and the LP's hydro classes carry no such attribute; biomass likewise.
The plan's charter names *"wind/solar/geothermal"*; adding `offshore_wind` is this memo's one
addition, because it is wind and the fleet types it separately — flagged in D-3c's
recommendation line so the owner can strike it.

### 4.2 Nuclear and CCS — owner box D-3c

Two of the four commitments in §3.3 row 11 are **carbon-free**, not renewable (Google's 24/7 CFE
counts nuclear; Microsoft's "100/100/0" counts carbon-free), and a "carbon-free" voluntary
program in the model would admit `nuclear` (and `gas_cc_ccs` at the policy capture fraction, if
the owner wants the federal CES's crediting convention, `federal_ces.py:166-171`). Mechanically
this is one line — the eligible set — because the clean-family resolver already admits nuclear
(`rows.py:153`). Substantively it changes what the dual **means**: with nuclear admitted, the row
in a nuclear-heavy ISO is slack at the fleet's existing output and the dual is zero until `V`
exceeds nuclear + VRE — the same crushing effect CX-6a fenced out of the REC dual
(`rows.py:59-69`). The recommendation is **renewable-only by default**, with a carbon-free
eligible set as an explicit `voluntary_eligible_fuels` override for a labelled arm, never the
default. A third leg of the same box: whether voluntary value is credited to **new builds
only** in the entry screen (§2.1's additionality note) — recommend **no** by default (the
market's annual REC claim has no vintage), owner may flip.

### 4.3 The netting rule against a federal CES — the brief for D-6

**When the question has content.** Under the CES **premium** ladder (`CES-P10/20/30`,
`federal_ces_enabled` + a premium) there is **no federal row** — the premium is a price
(`federal_ces.py:1-9`), so "netting" reduces to the price composition the screens already do
(`max()` of the premium and the voluntary dual; one certificate, sold to the higher buyer). D-6
has content only against WS-2a's CES **target** row (`CES-T80`), where two constraint rows can
both count the same MWh in dispatch.

**Posture 1 — counts toward (the plan's recommendation, `:783`).** The federal target row and
the voluntary row are independent constraints; a wind MWh satisfies both. This is the FFR-6B
§6.4 doctrine the repo already applies between the renewable and clean state rows
(`rows.py:1846-1850`): *"a wind MWh satisfying both its renewable row and its clean row is
CORRECT — two constraints, one MWh"*. Zero code beyond both rows existing. What it represents:
a standard measured on the **grid's generation share**, where voluntary procurement is one of
the ways the share moves — a voluntary buyer's claim does not raise the LSE's obligation.

**Posture 2 — additional.** The voluntary volume is added to the federal RHS
(`target(y) × Σ demand + V`), equivalently the voluntary row counts only MWh beyond the standard.
One RHS adjustment on the CES row when both are armed. What it represents: a **tradeable
certificate** design, where a certificate a corporate buyer retires voluntarily is unavailable
for compliance, so the LSE must retire another — the mechanics of every existing REC market
(a certificate cannot be retired twice), and the reason the voluntary market's own
"additionality" discourse exists.

**Recommendation, stated with its cost.** Default **counts-toward**, for three reasons: it is
the doctrine already in force between the state families; it is the reading under which the
model's *emissions* answer is not double-counted (both rows demand clean MWh; only the larger
binds); and it needs no code. The **honest counter** is that certificate mechanics favour
"additional" under a tradeable CES, so the campaign **reports both** (plan §3.5 `:689`,
`CES-P20+VOL-HI` — and, once WS-2a lands, `CES-T80+VOL-HI`) and the owner rules which is the
headline. A posture switch is needed to express "additional" in a committed config; that is the
fourth field of §5.1, and its owner (WS-2a's CES block or WS-3b's voluntary block) is a desk
routing question (§8), because it touches the CES row's RHS.

**What netting never does.** Neither posture changes the `max()` at the screens — a MWh's
attribute revenue is the higher single value under both. Netting is a **dispatch RHS** question
only.

---

## 5. Fields, coercion, cache key, registry surface, matrix duty

### 5.1 Fields (all in `ScenarioConfig`, cited; `constants.py` carries the anchors)

| field | type / default | semantics | inert value |
|---|---|---|---|
| `voluntary_clean_demand_path` | `str = "off"` | `"off" \| "low" \| "mid" \| "high"`; selects the `(s_base, f_commit)` trajectories from a `VOLUNTARY_CLEAN_DEMAND_ANCHORS` table with the `{year: value}` + low/mid/high grammar of `DATACENTER_ADDITIONS_MW`, resolved through `_effective_percentile` / `_interpolate_low_mid_high` (`scenario_resolvers.py:30-60`) at the neutral 0.5 percentile (no sampler lever added — G-L5 records the existing ones are never drawn) | `"off"` → `V = 0`, **no row built** |
| `voluntary_wtp_ceiling_usd_per_mwh` | `float \| None = None` | `None` → `constants.VOLUNTARY_WTP_CEILING_USD_PER_MWH[path]` (real 2026$, `REAL_DOLLAR_BASE_YEAR` convention); an explicit value overrides for a labelled sensitivity | `None`; consumed only when the path is not `"off"` |
| `voluntary_eligible_fuels` | `list[str] \| None = None` | `None` → the cited default set (§4.1); names validated against `FUEL_TYPE_MAP` at resolve time (hard error on unknown, `rows.py:193-198`) | `None` |
| *(D-6 posture)* `voluntary_counts_toward_ces` | `bool = True` | `True` = counts-toward (independent rows); `False` = additional (the CES target RHS gains `V`); **inert unless both rows are armed** | `True` |

The plan budgeted *"≤ 3 fields"* (`:548`); the fourth is the D-6 switch and is routed to the
desk rather than silently added (§8).

**`__post_init__` behaviour (WS-3b builds exactly this):**
- validate the path label, then **coerce to `"off"` when `mode == "backcast"` or `hindcast`** —
  the `datacenter_load_path` / `electrification_path` construction verbatim
  (`scenarios.py:15739-15746`, `:15758-15765`), with a standalone
  `validate_voluntary_config` hard-error on a non-off path reaching a scored backcast (the
  `datacenter.py:323` defense in depth). Coerce to the **dataclass default, never a literal**
  (`scenarios.py:15777-15805`, the FFR-3D hazard).
- `voluntary_wtp_ceiling_usd_per_mwh`, if given, must be `> 0` (a zero ceiling is a row with a
  free escape — the dual is pinned at zero and the row is inert; refuse loudly rather than
  build a no-op that looks armed).
- **Not suppressed by `federal_ces_replaces_state_rps`** (`federal_ces.py:508-520`): the
  voluntary buyer is not a state row and exists under any federal policy. Stated so the
  pure-federal counterfactual is *pure federal plus voluntary* in a `VOL-*` arm, which is what
  the arm means.
- No mutual-exclusion guard against the CES premium or target (they are different buyers;
  composition is the `max()`). The only cross-field guard is on the D-6 switch: `False` with no
  CES target row armed is a config error (there is nothing to be additional to).

### 5.2 Backcast byte-identity and the cache key

- **Coercion** (above) means no backcast or hindcast config can carry a non-off path; the LP
  kwargs for the family are passed `UNSET` when the row is off, exactly as the RPS and
  clean families are today (`runner.py:3113-3154`), so the dispatch-kwargs key set of every
  unarmed LP is unchanged.
- **Registration.** All four fields go into `_CACHE_KEY_OPTIONAL_FIELDS` (`scenarios.py:148`)
  with their inert defaults declared in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` (`:1482`) in the
  **same commit** (the nyiso-119 discipline; `scripts/check_cache_key_registration.py`
  enforces both directions). Result: `cache_key(ScenarioConfig())` and the bare backcast key
  are **byte-stable** (pinned by `tests/regression/test_persisted_identity.py`); an armed run
  hashes distinctly. No cache-epoch entry is needed — no default flips (`results/cache.py:57-86`
  is the ledger for the case where one does).
- **Proof is by test, never by solve.** WS-3b's byte-identity deliverable is the listed keys
  before/after plus the K=1/all-zones regression (`test_dispatch.py:1180-1193` pattern) and a
  trivial-first row test (1 generator / 1 zone / 24 h: binding → dual = the clean-minus-dirty
  marginal-cost gap; ceiling → dual = `w`, escape MWh = shortfall) — plan §3 WS-3 item 2.

### 5.3 Registry surface (rule 24)

Every value that can change a solve is a `ScenarioConfig` field or a cited `constants.py`
entry and appears verbatim in `run_config.json`; the resolver in `policy/voluntary_demand.py`
holds no literal, no per-ISO dict, no `getattr` fallback. The resolved `V(ISO, y)`, the
per-zone `frac`, the ceiling and the eligible set are written into the run's
`resolved_inputs` block (`data/resolved_inputs.py:368`) so what the LP was handed and what the
config says cannot disagree.

### 5.4 Runner and pipeline touch points (for WS-3b's file list; none touched here)

- `runner.py:2841-2864` — arming: build the voluntary region beside (or without) the state
  families; forecast-mode-only through the same gate style as `_rps_region_grain_active`
  (`:1195-1229`), never ISO-gated (the axis is ISO-agnostic; rule 25 lives in the anchors).
- `runner.py:3139-3154` — the family's LP kwargs (`UNSET` when off).
- `runner.py:4514-4521` — the dual → `clean_credit_by_fuel` mapping already carries any region
  count; the voluntary region's label (`"VOLUNTARY"`) rides `CleanRegionArrays.labels`
  (`clean_tiers.py:82`).
- `model.py:371-402`, `:1196-1219` — slot and dual arithmetic, **after** WS-2a's relaxation.
- `results/export.py` — expose the voluntary dual and escape MWh beside `rps_shadow_price`
  (the probe gate reads them, §6); WS-0 owns the emissions surface and is not touched.

### 5.5 Matrix duty (rule 28, CI-enforced)

In the **same PR** as the fields: a base row in `docs/codebase-site/data/mechanism-matrix.js`
(`id: "voluntary_clean_demand"`, `cat: "policy"`, `mode: "F"`, `def: "voluntary_clean_demand_path
:<line> (off in REF)"` — the `federal_ces` row's shape, `mechanism-matrix.js:2574-2576`) plus one
cell line in **every** ISO shard (`docs/codebase-site/data/mechanism-matrix/<ISO>.js`, the
`federal_ces: { cell: "O", fc: "O" }` shape at `ERCOT.js:309`): backcast `cell: "·"` (a
forecast-only axis is n/a in the keeper lane) and forecast `fc: "U"` until probed. WS-3c
re-stamps ERCOT's `fc` on its verdict. Shard edits are the **last commit**, one appended line
per ISO, after a fetch + rebase (ledger §4 protocol item 2). `scripts/check_mechanism_matrix.py
--base` fails the PR otherwise (`:32-40`).

---

## 6. The probe design and its structural gate (for SCN-WS3c's PRECOMMIT; no solve here)

**Instrument.** ERCOT 2026 **T0** (FF plan §2.1 `:230`: one solve-year, `run_full_horizon.py
--end-year 2026`), REF vs `voluntary_clean_demand_path=mid`, **only that field moved**. ERCOT is
the right first ISO for the reason the plan gives (`:592-594`): the largest DC block
(`constants.py:2867-2871`) and no state RPS row at all (`STATE_RPS_FLOORS["ERCOT"]` is all zero,
`capacity_market.py:4276`; `federal_ces_suppresses_state_rps` is moot there,
`federal_ces.py:515-516`), so the voluntary row is the **only** attribute driver and its
footprint is unconfounded. Energy-only (`capacity_market.py:1501`), so no RA leg complicates the
entry half.

**Control = the committed REF bundle** (rule 29(b)); WS-3c's PRECOMMIT carries the G-DRIFT audit
(`git diff <REF git_sha> HEAD -- src/market_sim …`, every hunk classified INERT or LIVE) and
spends a control solve only on a LIVE hunk.

**Phase 0, zero LP (rule 29 step 0), before any solve:**
1. `V(ERCOT, 2026)` from the resolver at `mid`, with each §3.3 cell's value and status printed.
2. From the REF bundle's committed 2026 outputs: eligible clean generation, curtailed clean
   energy (`results/export.py:151-153`, `curtailment_twh` `:205`), and the 2026 W+S potential
   (`CF × capacity`). Three numbers decide the arm's fate without a solve: if `V ≤` REF eligible
   generation the row is **slack and the mechanism is INERT in 2026** — screen it on the year
   its footprint is largest instead (rule 29's inert clause; the footprint is `V − clean_REF`
   over the T1-F window, computable from the REF bundle), and say so in the PRECOMMIT; if
   `V >` potential + escape economics say the escape must fire, the expected dual is `w`
   exactly and the expected shortfall is `V − potential`.
3. The predicted sign and order of magnitude of: Δcurtailment (≤ 0, bounded by REF
   curtailment), Δthermal generation (≈ −(ΔV_recovered − Δcurtailment)), ΔCO2 (< 0).

**Structural gate — STOP-only, never a residual, never promotes:**

| leg | check | source |
|---|---|---|
| G-BIND | the row binds **or** its escape fires; dual `∈ (0, w]` iff binding; dual `= w` iff `ESC > 0`; slack ⇒ dual `= 0` | exported dual + escape MWh |
| G-ID | `Σ eligible MWh + ESC ≥ V` holds to LP tolerance; `ESC = max(0, V − Σ eligible)` | the row's own arithmetic |
| G-ORDER | curtailment falls first: `Δdump(W+S) ≤ 0`, and the recovered clean MWh up to REF's curtailment come from the dump columns before thermal displacement | `curtailment_twh`, class energies |
| G-FOOT | displaced footprint confined to thermal classes; storage throughput and import-node flows move only by the second-order amount phase 0 predicted; no zone's slack (unserved) rises | class hourlies (`hourly/` sidecars) |
| G-CO2 | annual CO2 falls (a paired check in `scripts/check_forecast_invariants.py`, the P1 shape at `:899-910`, call it V1) | `emissions_mt` (WS-0's grain when it lands) |
| G-INV | no non-target load-bearing invariant flips PASS → FAIL (I1–I14 no-FAIL, FF plan §2.1 `:237`) | invariants |
| G-BYTE | backcast and hindcast keys unchanged — **by test, not by this solve** | §5.2 |

Any leg failing **kills the arm and is the session's result**; no leg passing promotes anything.
A gate that reads *"did the scenario look right"* is the fitted-mechanism selection rule 1
forbids.

**Deployment half.** Then ERCOT T1-F 2026–2030, REF + `VOL-MID` + `VOL-HI`, within the §2.1b
five-year cap (`:297-302`) and with no control solve: the voluntary dual must appear in the entry
screen's attribute `max()` (`new_entry.py:1118-1128`) and VRE entry in `VOL-*` must be ≥ REF's,
with the ERCOT solar-entry residual (R1) disclosed as a shared defect of both arms, never as a
result (plan §4 `:706-712`). Registered to the forecast namespace via
`scripts/register_forecast_run.py` (kind `scenario`, once WS-0 lands it), never the backcast
registry.

---

## 7. Decision boxes for the owner

Each box: question / recommendation / what it blocks / rule it touches / status.

**Box 1 — D-3 (PRESENTED r#1): is a voluntary clean-demand *scenario axis* admissible, given
ffr-5b §1.4's inadmissibility ruling on corporate PPA demand as a *driver*?**
- Recommendation: **YES** — a declared, forecast-only, publicly-anchored, default-off axis is a
  different admissibility class (§1); the ffr-5b null is preserved in REF and every scored lane.
- Blocks: SCN-WS3b entirely; the plan's `VOL-MID`, `VOL-HI`, `CES-P20+VOL-HI`, `ALL-CLEAN` cases.
- Rules: 13 `[R-MEASURED]`, 20 `[R-DOF]`, 24 `[R-REGISTRY]`.
- Status: OPEN; §1 is the brief.

**Box 2 — D-3b (in the plan's D-3 row): does in-LP hourly (24/7) matching stay deferred to the
isolated portfolio tool?**
- Recommendation: **YES, deferred** — LP-shape and portfolio-problem reasons (§2.2); feed the
  tool the `VOL-*` scenario LMPs instead.
- Blocks: nothing now; a later hourly-row lane if the owner wants one.
- Rules: 1 `[R-STRUCT]`, 2 `[R-VECTOR]`, 19 `[R-ONE-MECH]`; the tool's isolation boundary.
- Status: OPEN (new sub-box, named in the plan's D-3 row).

**Box 3 — D-3c (NEW): the eligible set — renewable-only by default (wind, solar, offshore wind,
geothermal), with nuclear / CCS only as an explicit "carbon-free" override for a labelled arm;
hydro and biomass excluded; and voluntary value credited to new builds only in the entry
screen, or to all eligible units?**
- Recommendation: renewable-only default incl. `offshore_wind` (strike it if the owner wants
  the charter's exact three); carbon-free set as an override, never the default (§4.2); credit
  all eligible units (no vintage gate), owner may flip.
- Blocks: WS-3b's `constants` default set and the resolver's fuel family (clean-family resolver
  needed the moment nuclear is admissible).
- Rules: 1, 19; CX-6a's REC-dual reasoning (`rows.py:59-69`).
- Status: OPEN (new).

**Box 4 — D-6 (PRESENTED r#1): netting between a federal CES *target* row and the voluntary
row — counts toward, or additional?**
- Recommendation: default **counts-toward** (independent rows, existing FFR-6B §6.4 doctrine,
  zero code); **additional** as the campaign's second reported posture; owner names the
  headline. Under the premium ladder the question is moot (§4.3).
- Blocks: the `CES-T80+VOL-HI` / `CES-P20+VOL-HI` "both ways" report; the fourth field's
  existence and owner (routing, §8).
- Rules: 19 `[R-ONE-MECH]`; plan §4 attribute double-claiming clause (`:722-727`).
- Status: OPEN; §4.3 is the brief.

**Box 5 — D-2 (PRESENTED r#1), the voluntary sub-levels: the low/mid/high pairs for `s_base`
(§3.3 row 8), the committed DC share `f_commit` (row 12), and the WTP ceiling (row 14).**
- Recommendation: `f_commit` low 0 / high 1.0 / mid owner-set; `s_base` mid = the latest NREL
  national share held flat, low/high = the report's own historical range; WTP from the public
  REC range with the ceiling itself owner-set. Every value in `constants.py` with the citation
  and its status column.
- Blocks: WS-3b's `constants` table (it can be built with placeholders labelled `needs-citation`
  but the probe cannot be quoted until the levels are signed).
- Rules: 5 `[R-NO-MAGIC]`, 13, 25 `[R-ISO-SCOPE]`.
- Status: OPEN (part of D-2).

**Nothing else needs a signature.** The EIA-861 intake is public data and needs no box (rule 22
clarification); the fourth-field question is desk routing, not an owner decision.

---

## 8. What this memo does not do, and the routing note

**The plan §5.1 Voluntary column is UNMOVED.** Criterion 1 (expressible in committed config),
2 (reaches dispatch + deployment), 3 (paired probe), 4 (byte-identity), 5 (matrix), 7
(registered) all still read **no / —**. A memo proves nothing; WS-3b moves rows 1, 2, 4, 5 with
tests and WS-3c moves 3 and 7 with a registered probe. This lane touches neither the plan's
§5.1 nor the ledger's §3 copy, by charter.

**Routing note (one paragraph, for SCN-DESK).** *Boxes the desk presents:* Box 1 (D-3 — already
presented; this memo is its brief), Box 2 (D-3b — a sub-box of D-3 the plan names), **Box 3 (D-3c
— new, eligibility)**, Box 4 (D-6 — already presented; §4.3 is its brief), Box 5 (the voluntary
sub-levels of D-2). *What SCN-WS3b consumes:* §2.1 (the "one more region of the clean family"
construction, all-zone mask, volume-as-fraction resolver, WTP as the region's ACP entry), §3.1–
§3.2 (the resolver arithmetic and allocation), §3.3 (the constants table with its status
column), §4.1 defaults, §5.1–§5.5 (fields, coercion, cache registration, registry surface,
matrix duty), §6's trivial-first tests — all **after** Box 1 is YES and Boxes 3–5 are signed;
Box 2 does not gate it. *Three items the desk must decide or relay, none of which this lane may
touch:* (a) **the fourth field** (`voluntary_counts_toward_ces`) exceeds the plan's ≤ 3 budget
and adjusts the CES *target* row's RHS — assign it to WS-2a's CES block or WS-3b's voluntary
block and say which; (b) **the shared construction** — SCN-WS2a is live now and should be told
that WS-3b intends to ride its relaxation as *an additional region of the clean family with an
all-zone mask*, so WS-2a's federal row can be built the same way and the relaxation is written
once (if WS-2a lands a different seam, §2.1 is re-pointed at it and this memo gets an
addendum); (c) **the EIA-861 state × sector sales intake** (one public CSV, not on disk) belongs
in WS-3b's data profile as ordinary data intake, no authorization needed. No file outside this
memo was touched, no solve was run, no default moved, no matrix cell written.
