# FFR-6B — The RPS row's spatial grain (E-1) and the clean/carbon-free tiers (E-2)

**Lane:** structural scoping (owner signature, sitting Addendum U.5, 2026-08-05). **Design only.**
No code, no `ScenarioConfig` field, no schema, no solve, no matrix cell, no dashboard contact. The
deliverable is a design plus an implementation card, on the FFR-5B pattern. The escalation record is
`docs/handoffs/ffr-5b-procurement-channel-design-2026-08-05.md` §5.3 (E-1/E-2) and §5.4 (the rider).

**Head at start:** `origin/main` `57120845` (the prompt's `8693b75d` had moved; the branch was reset
onto the later head before any work). **State re-verified at this session's own head, from the shards
themselves:** keepers ERCOT `2026-08-05-run168b-year-curves` · PJM `2026-08-04-pjm-152-collapse` ·
CAISO `2026-08-05-caiso-174-measured-fleet` · NYISO `2026-08-04-nyiso-125-seam-envelope` · NEISO
`2026-08-05-neiso-83-ca1-reclass` · MISO `2026-08-05-miso-132b-cc-committed`. `complete` =
{CAISO, NEISO, NYISO, PJM}; `final` block holds only its `_note` (EMPTY). Holdout freeze **active**
and irrelevant to this lane — nothing here solves, scores or touches a year.

**What is measured here, and where it came from.** Every number below is computed from committed
on-disk artifacts (eGRID 2023 `PLNT23`, EIA-930 region parquets, the EIA-860 vintage + canonical
sheets) mapped through **the repo's own** `data/zone_assignment.assign_zone` and
`config/iso_configs` load shares, or read off source at head. No LP was solved. Reproduction: §10.

---

## 0. Headline

Four findings, in descending order of consequence. The first three were not the findings this lane
expected to make.

1. **E-1's diagnosis needs one correction before it can be implemented, and the correction changes
   the design.** The defect is *not* that the row is ISO-wide. It is that the row's **compliance
   region** is assumed to be the ISO in all five RPS-carrying ISOs, when that is a **per-state
   statutory fact** that happens to be true in four of them and false in the fifth. PJM Class I RECs
   trade footprint-wide (the "PJM Tri/Quad-Qualified REC" products exist because PA/NJ/MD/DC accept
   the same PJM-region generation); MA Class I eligibility is the ISO-NE control area (225 CMR
   14.05); NY Tier 1 is the NYCA; CAISO is one obligated state. **For those four, one ISO-wide row is
   arithmetically EXACT, not a dilution** — under free intra-footprint REC trade,
   `Σ_s target_s × load_s` *is* `blend × total_load`, which is what the code already builds.
   **MISO is the exception**, and it is the whole of E-1.
2. **In MISO the dissolution is real and I measured it.** MISO's zones are exact unions of whole
   states, so a zonal row *is* a state-group row. At that grain **MISO-East's obligation is 0.328 of
   zone load against a measured 0.081 VRE share (2023) — a 24.7 pp deficit on 24 % of ISO load —
   while MISO-Plains runs a 41.5 pp surplus against a 0.064 obligation.** The single ISO-wide row
   sees 0.158 against a 0.16 target and is satisfied to within 0.2 pp. **Iowa's surplus is paying
   Michigan's bill, and Michigan's statute forbids exactly that** (MCL 460.1029: credits must come
   from systems "located within this state"). The aggregation is a dilution *in MISO* because
   MISO's REC market is not free.
3. **E-2 is adjudicated: the clean/carbon-free row BINDS, and it binds only at E-1's grain.** MISO
   ISO-wide clean generation is 0.320 of load against a load-weighted clean obligation of 0.091
   (2030) / 0.212 (2035) / 0.251 (2040) — **slack in every year**. At zone grain **MISO-West is
   short 14.0 pp by 2030 rising to 29.4 pp by 2040, and MISO-East is short 21.7 pp by 2035 rising to
   33.1 pp by 2040.** So the answer to FFR-5B's open question ("or would it merely be slack for the
   same aggregation reason as E-1?") is: **slack if built ISO-wide, materially binding if built at
   the state-group grain E-1 produces — which is exactly why the owner ordered them settled
   together.** Build it, and only after E-1.
4. **A defect neither E-1 nor E-2 was looking for, larger in dollar terms than both.** Three of the
   five RPS-carrying ISOs encode a **clean/zero-emission** target on the **renewable-only (wind +
   solar)** row: NYISO's `2040: 1.00` is the CLCPA zero-emission standard, NEISO's whole trajectory
   is self-described in code as a "CES blend", and CAISO's `2040: 0.80 / 2045: 1.00` is SB 100's
   zero-carbon path, not its RPS. Compounding it, the eligible set is wind+solar only where the
   governing statute counts more: **NYISO's row omits 20.2 pp of statutorily-countable generation
   (existing hydro), CAISO's omits 7.1 pp (geothermal, biomass, small hydro).** The consequence is
   not a small mis-level — it pins those rows' duals at the ACP ceiling for the whole horizon, and
   `rps_shadow_price` is credited to every new VRE candidate in `apply_economic_new_entry`. **A
   permanent, mechanism-generated $40–50/MWh entry subsidy in three ISOs is the single largest
   forecast-behaviour consequence in this document, and it is a level/eligibility bug, not a grain
   bug.** It should be fixed *before* E-1, because it is cheaper, more certain and larger.

**Free parameters proposed in total: none.** Every quantity in both designs is a statutory level, a
statutory eligibility set, or a measured load share — each with a citation (§3.4, §6.4).

**Rider (§9).** The FFR-5B §5.4 residual is sized. At the channel's own `U/V/TS` basis and its most
favourable horizon (*h*=1), the 2021–2025 cumulative unrepresented VRE build is **MISO 11.1 GW,
PJM 7.9 GW, ERCOT 13.2 GW, CAISO 5.4 GW, NYISO 2.2 GW, NEISO 1.1 GW.** The method reproduces
FFR-5B's MISO figure exactly (18,649 MW solar 2021–25), which is the cross-check that it is
measuring the same object.

---

## 1. E-1 — verifying the reconciliation claim at implementation grain

FFR-5B §5.3 states: *"The per-state → per-zone reconciliation needed for a zonal row is already
derived inside `STATE_RPS_FLOORS["MISO"]`'s own comment block."* This lane's first duty was to
verify that claim for **every** multi-state ISO, at the grain an implementer would need, rather than
assume it. It verifies for MISO and **fails for the other two multi-state ISOs**.

### 1.1 Which ISOs are multi-state at all

Read from `config/iso_configs.py` at head, not assumed:

| ISO | zones | states in the obligated footprint | E-1 applies? |
|---|---|---|---|
| **ERCOT** | 7 (6 carry load) | TX | **No** — `STATE_RPS_FLOORS["ERCOT"]` is all-zero; no row is built. |
| **CAISO** | 3 + `WECC_import` | CA (obligated); AZ/NV host resources only | **No** — one obligated state, one obligation. |
| **NYISO** | 5 | NY (obligated); a little NJ generation | **No** — one obligated state. Verified, not assumed. |
| **NEISO** | 4 + `HQ_import` | ME, NH, VT, MA, RI, CT | **Yes, structurally** — but see §2. |
| **PJM** | 8 | IL, IN, MI, KY, TN, OH, PA, WV, MD, DC, DE, NJ, VA, NC | **Yes, structurally** — but see §2. |
| **MISO** | 6 | MN, ND, SD, MT, IA, MO, IL, IN, KY, WI, MI, AR, LA, MS, TX | **Yes, and materially** — §2.2. |

### 1.2 Whether zones are unions of whole states — the property the whole design turns on

**MISO: YES, exactly.** `zone_assignment._MISO_STATE_ZONES` is a pure FIPS-state → zone map with no
lat/lon split, and its own comment says so: *"Every zone is an exact union of whole states."* Zones
are whole EIA-930 sub-BA (LRZ) unions. Verified against the data: the zone × state generation
crosswalk has **exactly one zone per state** for all 15 MISO states (§10 output C).

**PJM: NO.** `_PJM_STATE_ZONES` covers only the states that fall cleanly inside one zone; **OH, PA,
MD and WV are deliberately absent and split by latitude/longitude/county** inside `_pjm_zone`
(`_PJM_OH_ATSI_LAT` 40.9, `_PJM_WV_NORTH_LAT` 39.0, `_PJM_PA_WEST_LON` −79.0, `_PJM_MD_WEST_LON`
−78.5, `PJM_PHILLY_COUNTIES`). Measured (2023 net generation, TWh): **PA's 235.9 splits across three
zones** (Central_PA 139.7 / West_APS 56.5 / EMAAC 39.8), **OH's 133.1 across two** (AEP_Ohio 94.8 /
ATSI 38.4), **WV's 52.3 across two** (West_APS 36.8 / AEP_Ohio 15.5), **MD's 36.0 across two**. A
PJM zonal row would therefore correspond to **no statutory compliance region whatsoever** — it would
cut Pennsylvania's AEPS obligation into three pieces and give each a different shadow price.

**NEISO: PARTIALLY.** Boston (NEMA) is wholly MA and Connecticut is wholly CT, but **North is
ME+NH+VT and Central is MA(W/SE)+RI**. Two of four zones are multi-state, and neither is a whole
state.

### 1.3 Whether the per-state obligation trajectories exist in the repo

| ISO | per-state trajectories in code/comment? | per-state → per-zone load split? | verdict |
|---|---|---|---|
| **MISO** | **YES, enumerated**: MN `.26→.40→.55→.55`, MI `.35→.50→.60→.60`, IL `.25→.40→.50→.50`, MO/MT `.15`, WI `.10`, IA/IN/KY/ND/SD/AR/LA/MS/TX `0` — each with its statute (`Minn. Stat. §216B.1691`, `2023 PA 235`, `CEJA / 20 ILCS 3855`, `RSMo §393.1030`, `Wis. Stat. §196.378`) | **YES, cited**: zone load shares from `iso_configs` + within-zone EIA-861 2023 retail-sales splits **MN ≈ .77 of West, IA ≈ .57 of Plains, MI ≈ .57 of East** | **CLAIM VERIFIED** (with one bounded gap, §1.4) |
| **PJM** | **NO.** The comment names states and directions ("NJ/MD 50% by 2030, IL 40%, DC 87%, VA ~37%, MI 40%", "PA/OH flat ~8%") but **enumerates no trajectory** and cites them collectively to an external PDF (PJM-EIS *Comparison of RPS Programs in PJM States*, 4/15/2025) that is **not on disk** | **NO.** It carries ISO-wide state *load weights* (OH 20.1 / PA 18.9 / VA 17.6 / …) sourced to `PJM_Load_by_State_2024_20250716.XLS`, which is **not on disk**. There is no state → zone load split anywhere | **CLAIM FAILS** |
| **NEISO** | **NO.** The floors comment is one line — "MA Clean Energy Standard + regional state CES blend" — with no per-state trajectory at all. (The *ACP* block separately carries state load shares MA ≈ 48 / CT ≈ 24 / NH ≈ 9 / ME ≈ 9 / RI ≈ 6 / VT ≈ 4 %, ISO-wide, not per zone) | **NO** | **CLAIM FAILS** |

### 1.4 The one bounded gap inside the verified MISO case

MISO-West is MN/ND/SD/MT with **MN ≈ .77** cited; the residual **.23 is not decomposed** among
ND/SD/MT. ND and SD have voluntary goals (0); **MT carries a 15 % standard**, so the zone obligation
is bracketed by MT taking none or all of the residual: **±0.0345** on one zone's target. That is the
entire unresolved quantity in MISO's reconciliation, it is bounded, and it is one line of EIA-861 to
close. **It does not block implementation** — the bracket is smaller than the effect being
represented by an order of magnitude (§2.2).

### 1.5 An independent check that the cited derivation is arithmetically sound

Re-blending the per-state trajectories onto the model's own zone load shares and the three cited
within-zone splits reproduces the ISO knots the code ships:

| knot year | re-blended from the comment's own parts | knot in `STATE_RPS_FLOORS["MISO"]` |
|---|---|---|
| 2026 | **0.1139** | 0.11 |
| 2030 | **0.1606** | 0.16 |
| 2040 | **0.1981** | 0.20 |

This is a genuine rule-14 verification, not a restatement: the ISO-wide constant and the per-zone
decomposition are consistent to <0.5 pp, so **the zonal design does not change the ISO's total
obligation — it only stops it being met in the wrong place.**

### 1.6 What intake E-1 needs, per ISO

* **MISO — none.** Implementable from committed artifacts + the cited comment block today. (The
  §1.4 MT bracket is optional polish.)
* **PJM — a per-state renewable-tier trajectory intake + a state-load intake**, and even with both
  the zonal design is refused on structure (§2.1/§5). *E-1 is not what PJM needs.*
* **NEISO — the same two intakes**, and the same structural refusal.
* **CAISO / NYISO / ERCOT — n/a.**

---

## 2. E-1 — what the defect actually is

### 2.1 The correction: compliance region ≠ model zone, and it usually equals the ISO

An RPS obligates **load** (a state's retail sales) and is discharged with **RECs**, whose
**geographic eligibility is set by each state's own statute**. That eligibility region — not the
model zone, and not the state — is the correct row boundary. Verified per ISO:

* **PJM — footprint-wide.** Class I RECs eligible in PA, NJ and MD are traded as a single
  *PJM Tri-Qualified* (and Quad-Qualified) product precisely because those states accept the same
  PJM-region generation; NJ (N.J.A.C. 14:8-2.3) explicitly authorizes Class I RECs from units
  "located within the PJM region but not connected to the New Jersey distribution system", and
  Maryland's Tier 1 (Md. Code, Pub. Util. §7-701 *et seq.*) accepts generation in PJM or a state
  adjacent to it. **One ISO-wide row is exact.**
* **NEISO — footprint-wide.** MA RPS Class I (225 CMR 14.05) qualifies units in the **ISO-NE Control
  Area**, or in an adjacent control area with energy scheduled and delivered into ISO-NE, tracked
  region-wide in NEPOOL GIS. **One ISO-wide row is exact.**
* **NYISO — the NYCA.** NY's CES Tier 1 obligation is discharged with NYCA-sited generation. The
  NYCA *is* the model's NYISO. **One ISO-wide row is exact.**
* **CAISO — one obligated state.** (CA's portfolio-content-category structure restricts *import*
  form, not intra-footprint trade; it is an import-eligibility question, not a grain question.)
* **MISO — NOT footprint-wide.** Michigan's standard is location-restricted to systems "located
  within this state" (MCL 460.1029, tracked in MIRECS, a Michigan-only registry); Illinois's CEJA
  obligation is discharged through centralized IPA procurement with in-state/adjacent-state
  requirements, not a fungible ISO-wide certificate; Minnesota's §216B.1691 standard is a
  delivered-to-Minnesota-retail-customers obligation met by vertically-integrated self-supply.
  **There is no MISO-wide REC market in which an Arkansas or Iowa certificate discharges a Michigan
  obligation.**

**So the mechanism of the defect is not aggregation per se — it is that a single row silently
asserts free intra-ISO REC trade, which is true in four ISOs and false in MISO.** This matters for
the design: a "zonal row" is the right instrument only where zone boundaries and eligibility
boundaries coincide, and E-1 must be scoped on that test rather than on multi-statehood.

### 2.2 The MISO measurement — the dissolution, quantified

Measured VRE share is eGRID 2023 in-zone wind + solar net generation over (EIA-930 2023 MISO demand
× the zone's `iso_configs` load share). Obligation is the §1.5 re-blend.

| zone | load share | VRE / load (2023) | obligation 2026 | 2030 | 2035 | **gap at 2030** |
|---|---|---|---|---|---|---|
| MISO-West (MN/ND/SD/MT) | 0.147 | 0.329 | 0.200 | 0.308 | 0.424 | −0.021 (binds by 2035: **+0.095**) |
| MISO-Plains (IA/MO) | 0.138 | **0.480** | 0.064 | 0.064 | 0.064 | **−0.415 (surplus)** |
| MISO-Illinois (IL) | 0.068 | 0.223 | 0.250 | 0.400 | 0.450 | **+0.177** |
| MISO-Indiana (IN/KY) | 0.134 | 0.051 | 0.000 | 0.000 | 0.000 | −0.051 |
| **MISO-East (WI/MI)** | **0.242** | **0.081** | 0.242 | **0.328** | 0.385 | **+0.247** |
| MISO-South (AR/LA/MS/TX) | 0.271 | 0.008 | 0.000 | 0.000 | 0.000 | −0.008 |
| **ISO-wide (the row today)** | 1.000 | **0.158** | 0.110 | **0.160** | — | **+0.002** |

Read the last two rows together. **The ISO-wide row is satisfied to within 0.2 pp; the zone carrying
24 % of MISO's load is short by 24.7 pp.** The arithmetic that reconciles them is MISO-Plains'
41.5 pp surplus — Iowa, a state with **no** binding RPS, supplying the certificates that make
Michigan's and Illinois's obligations look met. That transfer is exactly what MCL 460.1029 forbids,
and it is the entire content of E-1.

**Where this is conservative.** eGRID's plant sheet is front-of-meter only, so distributed solar is
absent from the numerator in every zone; and the denominator is model zone load, not retail sales.
Both push measured shares *down*. Neither can plausibly close a 24.7 pp gap in MISO-East (Michigan's
utility-scale wind is in the numerator already), and both apply equally to the ISO-wide row, so the
*contrast* — the thing being demonstrated — is unaffected.

---

## 3. E-1 — the design

### 3.1 The generalization, in one sentence

Generalize `_build_rps_row` from *one row over all renewable columns* to **K rows, each carrying (a)
an eligibility mask over zones and (b) its own RHS and ACP price** — with today's behaviour as the
`K = 1, mask = all zones` special case, which is what **four of five RPS ISOs keep, byte-identically**.

```
for each compliance region r:
    Σ_{z ∈ eligible_zones(r)} Σ_t ( W[z,t] + S[z,t] )  +  Σ_t ACP_r[t]
        ≥  Σ_{z ∈ obligated_zones(r)} target_r,z × Σ_t demand[z,t]
```

Two masks, deliberately distinct:

* **`obligated_zones(r)`** — where the *load* carrying the obligation sits. Sets the RHS.
* **`eligible_zones(r)`** — where a certificate may be *generated*. Sets the LHS.

They coincide for a location-restricted standard (Michigan) and diverge for a delivery-based or
footprint-wide one (Minnesota, and every PJM/NEISO state). **Keeping them separate is what makes the
same structure express both, and what makes the four unaffected ISOs a literal special case rather
than a re-derivation.** A design that fused them into "one row per zone" would be wrong on its face:
measured 2023 in-zone VRE/load runs from **0.0002 in NYC to 2.80 in CAISO SP15_rest** — generation
sits where the resource is, load where the people are, and no RPS in the country requires them to
match.

### 3.2 What the dual means at each grain

Today's dual is *the* REC price. Under K rows, **row r's dual is the REC price of compliance market
r** — the marginal $/MWh a certificate eligible in region r commands. That is the correct economic
object and it is directly observable in the real world (MIRECS-registered Michigan RECs and M-RETS
Iowa RECs are different products at different prices; PJM Tri-Qualified RECs are one product at one
price). The dual is still capped at that region's own ACP by its own escape column.

**The consumer seam must be updated with the row count.** `rps_shadow_price` is currently a scalar
(`lp/model.py:1003–1006`) consumed by `apply_economic_new_entry` (`new_entry.py:935, 1111`) and the
retirement screen (`retirements.py:1961`) as a flat per-MWh attribute credit for
`_RENEWABLE_NEW_FUELS`. Under K rows it becomes **per-zone**: a candidate in zone z earns
`max over r of {dual_r : z ∈ eligible_zones(r)}`. **A scalar left in place would silently broadcast
MISO-East's high dual to an Arkansas candidate and build the MW in the wrong zone — the failure mode
that makes this correction worth making would be reintroduced downstream of the row that fixed it.**
This is a required part of the change, not a follow-up.

### 3.3 Where the rows attach in the matrix

`build_constraints` (`lp/rows.py:1558–1568`) appends the RPS row between the mass-cap block and the
reserve block, and `model.py` recovers the dual end-anchored (`rps_idx = -1 - n_reserve_rows`). K
rows occupy that same slot as a contiguous block; the recovery becomes a slice of length K at the
same anchor. `_build_rps_row` already assembles from `np.arange`/`ravel` column-index arithmetic with
no hour loop, and per-row masking is a zone-index filter on the same expression — **rule 2
`[R-VECTOR]` is satisfied by construction, with the only Python loop being over K ≤ 6 rows, the same
shape as `_build_mass_cap_rows`' loop over caps.**

### 3.4 Every proposed constant, with its citation (rule 5)

Nothing here is fitted; each is a statutory level or a measured load share. Only the MISO set is
proposed for the first implementation (§5).

| quantity | value | source |
|---|---|---|
| MN renewable tier | 55 % by 2035 (ramp `.26/.40/.55/.55` at 2026/30/40/45) | Minn. Stat. §216B.1691 (2023 HF7) — already in `STATE_RPS_FLOORS` comment |
| MI renewable tier | 50 % by 2030, 60 % by 2035 | 2023 PA 235 (SB 271), MCL 460.1028 — already in comment |
| IL renewable tier | 40 % by 2030, 50 % by 2040 | CEJA, P.A. 102-0662 / 20 ILCS 3855 — already in comment |
| MO / MT / WI tiers | 15 % / 15 % / 10 %, flat | RSMo §393.1030; Mont. RPS; Wis. Stat. §196.378 — already in comment |
| IA, ND, SD, IN, KY, AR, LA, MS, TX | 0 | no binding standard — already in comment |
| zone load shares | West .1466, Plains .1385, Illinois .0676, Indiana .1340, East .2422, South .2711 | `iso_configs._miso_config`, measured EIA-930 sub-BA 2023–25 energy shares |
| within-zone state splits | MN .77 of West; IA .57 of Plains; MI .57 of East | EIA-861 2023 retail sales restricted to the MISO-served portion — cited in `STATE_RPS_FLOORS["MISO"]`; **source file not on disk** (§1.4) |
| MI eligibility mask | MISO-East only | MCL 460.1029 ("located within this state"); MIRECS |
| IL eligibility mask | MISO-Illinois (+ adjacent, if the implementer prefers the wider reading) | CEJA centralized IPA procurement |
| MN eligibility mask | MISO Midwest footprint | Minn. Stat. §216B.1691 delivery construction |
| ACP | MISO $30/MWh (existing) | `STATE_RPS_ACP`; per-region ACPs are a refinement, not a requirement |

---

## 4. LP size and degeneracy (rule 2)

**Rows.** +(K−1). For MISO K=6 → **+5 rows** against 52,560 energy-balance rows alone. Immaterial.

**Non-zeros.** **Unchanged.** Every renewable column appears in exactly one row under a partition of
the zones, so the total nnz of the RPS block is identical to today's; a *delivery*-based mask that
overlaps another region's puts one column in two rows, bounded above by K × (today's nnz) and in
practice ≈2× for one row.

**Columns — the only real cost, and it is a pre-existing structure worth understanding before
touching.** The ACP escape is **one column per hour** (`rows.py:71`), i.e. 8,760 columns carrying
+1 in a single *annual* row at an identical objective cost. Those 8,760 columns are mutually
interchangeable — a pure primal degeneracy — but the structure is **required, not an oversight**:
the layout is strictly `T × vars_per_hour` (`layout.py`), so there is nowhere to put a single annual
scalar. K regions therefore cost **K × T ACP columns** (MISO: 52,560, of which 43,800 are new), on a
per-plant MISO layout whose total column count is in the millions — well under 1 %.

**Degeneracy.** No *new* degeneracy is introduced, and the existing kind is not made worse in a way
that matters: the interchangeable ACP columns leave the row's dual well-determined (it is pinned at
min(marginal eligible-VRE cost, ACP) whichever column absorbs the escape), and that property is
per-row, so it holds for all K. **The one genuinely new degeneracy risk is an overlapping
eligibility mask**: if two regions accept the same certificate and both rows bind, the split of that
generator's MWh between them is arbitrary while the *duals* remain determinate. That is economically
correct (one certificate, one sale, two possible buyers at the same clearing price) and is the same
structure the objective's ε-tiebreaker handles elsewhere; it needs no new tiebreaker, but an
implementation should not report a per-row "MWh allocated" quantity as if it were meaningful.

**Cache/byte-identity.** Changing `n_rec_acp` from 1 to K changes the layout for the affected ISO and
therefore its cache key. **Four ISOs must be byte-identical, and the `K = 1` default guarantees it.**
Verify with the existing regression pattern before promotion.

---

## 5. Interaction with the surrounding architecture

### 5.1 With "RPS is not a force-build step" (CLAUDE.md steps 4–5)

**Unchanged and reinforced.** The correction is entirely inside the LP constraint. No step gains a
build action, no MW is forced, and the only channel from the row to capacity evolution remains the
dual → `rps_shadow_price` → the *screen's* margin. Making that dual **locational** is precisely what
lets the constraint-not-a-force-build architecture site VRE correctly: today a satisfied ISO-wide row
sends a zero signal everywhere; tomorrow MISO-East sends a real signal and MISO-South keeps sending
zero — through the screen's own economics, which is the architecture working, not being bypassed.

### 5.2 Rule 19 `[R-ONE-MECH]` — full enumeration of what already pays the same MWh

Every mechanism that can pay a renewable MWh today, and how double-counting is excluded:

| mechanism | what it pays | exclusion |
|---|---|---|
| **The RPS row's own dual** | eligible wind/solar | This lane **replaces** it at a different grain; it is not stacked. One row family, one phenomenon. |
| `eac_price_wind` / `eac_price_solar` | exogenous $/MWh REC | **Already no-stacked** by the house doctrine — one certificate, sold once, `max(eac, rps_shadow)` (`policy/eac.py` docstring; `retirements.py:367`). **Requirement:** the `max()` must be taken against **that zone's** dual, never a broadcast scalar (§3.2). |
| `federal_ces_*` premium | federal CES EAC | Already no-stacked by the same `max()` (`federal_ces.effective_unit_eac_prices`), and `federal_ces_replaces_state_rps` already suppresses the state rows wholesale (`runner.py:2040`). **K rows inherit both unchanged.** |
| IRA §45/48 PTC/ITC (`policy/ira.py`) | production/investment subsidy | **Legitimately stacks** — a PTC-eligible wind farm also sells RECs in the real market. Existing decision; not disturbed. |
| **FFR-5E's procurement channel** (D-18, if chartered) | supplies **MW** | See §5.3. |
| Reserve-margin backstop, capacity deliverability | capacity, not energy attributes | Orthogonal. |

### 5.3 The double-count exclusion statement for FFR-5E (rule 19, stated as the prompt requires)

**The two mechanisms cannot double-count the same MW, and here is why, mechanically rather than by
assertion.**

* **They act on different objects.** The FFR-5E channel *supplies capacity* — it writes MW into
  `renewable_additions[zone][tech]` at step 4. The RPS row *demands energy* — it constrains MWh in
  the dispatch LP. Neither reads the other's output: the channel does not consult
  `rps_shadow_price`, and the row does not build MW.
* **They compose in the correct direction, through the LP.** A MW the channel injects raises the
  eligible VRE available to its own zone's row, **relieves** that row, and **lowers** the dual —
  which **reduces** the economic screen's VRE entry by exactly the value of the certificates that MW
  now supplies. Under a single ISO-wide row that relief is smeared across the footprint; **under K
  rows it lands in the region that actually gained the resource**, which is strictly more correct.
  This is the same argument FFR-5B §2.4 makes, and the grain correction improves it.
* **The one thing that would break it, named so it cannot happen by accident.** If a future
  implementation ever gave the RPS row a *build* limb — "force-build to satisfy the shortfall" —
  that limb and the procurement channel would both create MW against the same statutory driver, and
  **that is the stacked mechanism rule 19 forbids.** FFR-5B already refused a policy-procurement
  channel on exactly this ground (§1.2). **E-1 must never acquire a build limb.** The RPS row's only
  legitimate output is a price.
* **Attribution keeps it auditable.** FFR-5E's `source: "procured"` tag and the screen's
  `source: "economic"` tag remain sufficient to attribute every MW; the zonal dual becomes a second
  observable that makes the *reason* for an economic MW attributable to a specific compliance region.

### 5.4 The stale comment found on the way

`runner.py:2036-2039` and `federal_ces.py:466` both assert the CES suppression is *"moot for ERCOT/PJM,
which carry no RPS row."* **PJM has carried a `STATE_RPS_FLOORS` entry (0.185 → 0.33) since the
FF-1E-policy refresh, so PJM does build a row and the suppression is not moot there.** Flagged for
the implementation PR to fix in passing; not fixed here (design-only lane).

---

## 6. E-2 — the clean / carbon-free tiers, adjudicated ex-ante

### 6.1 What the statutes actually are (the three MISO tiers, cited)

| state | clean / carbon-free tier | counts | statute |
|---|---|---|---|
| **MN** | **80 % by 2030** (IOU; 60 % other), **90 % by 2035**, **100 % by 2040** | carbon-free: nuclear, hydro, wind, solar, hydrogen, biomass | Minn. Stat. §216B.1691 subd. 2g (2023 HF7, eff. 2023-02-08) |
| **MI** | **80 % by 2035**, **100 % by 2040** | clean: nuclear + renewables (+ qualified CCS gas) | 2023 PA 235 (SB 271) |
| **IL** | **no dated LSE percentage obligation** — CEJA sets a *state policy goal* of 100 % clean by 2050 plus dated **fossil-emission phase-outs**, which is a different instrument | — | P.A. 102-0662 |

**IL is a null and should be recorded as one.** Illinois's decarbonization is a source-side emission
schedule, not a share obligation on load-serving entities, so **it must not get a clean row** — a row
would be inventing an obligation the statute does not impose. (MI's 80 %-by-2035 interim is *missing*
from the existing code comment, which records only "100 %-clean-by-2040"; it is the knot that makes
MISO-East bind five years earlier than it otherwise would.)

### 6.2 The ex-ante bind/slack adjudication — measured, at both grains

Clean share is eGRID 2023 in-zone (wind + solar + nuclear + hydro + biomass + geothermal) over zone
load. Obligation is the state tier × that state's within-zone load share (§3.4 splits).

| zone | clean / load (2023) | oblig 2030 | gap | oblig 2035 | gap | oblig 2040 | **gap 2040** |
|---|---|---|---|---|---|---|---|
| **MISO-West** (MN .77) | 0.476 | 0.616 | **+0.140** | 0.693 | **+0.217** | 0.770 | **+0.294** |
| **MISO-East** (MI .57) | 0.239 | 0.000 | −0.239 | 0.456 | **+0.217** | 0.570 | **+0.331** |
| MISO-Illinois | 0.413 | 0.000 | — | 0.000 | — | 0.000 | — (no obligation, §6.1) |
| MISO-Plains | 0.598 | 0.000 | −0.598 | 0.000 | −0.598 | 0.000 | −0.598 |
| MISO-Indiana | 0.072 | 0.000 | −0.072 | 0.000 | −0.072 | 0.000 | −0.072 |
| MISO-South | 0.265 | 0.000 | −0.265 | 0.000 | −0.265 | 0.000 | −0.265 |
| **ISO-wide** | **0.320** | 0.091 | **−0.229** | 0.212 | **−0.108** | 0.251 | **−0.069** |

**Verdict: BUILD IT — but only at E-1's grain, and only after E-1.**

* Built **ISO-wide**, the clean row is **slack in every modelled year through 2040** (−22.9 pp
  falling to −6.9 pp). FFR-5B's hypothesis — that it might be slack for the same aggregation reason
  as E-1 — is **confirmed for the ISO-wide form**. Building it that way would add a row, add an ACP
  column block, add a `ScenarioConfig` field and change nothing: an inert mechanism, which rule 19
  and the matrix's `I` verdict exist to catch.
* Built at **state-group grain**, it binds **materially in two zones covering 39 % of MISO load**,
  from **2030** (West) and **2035** (East), reaching **+29 pp and +33 pp by 2040**. These are not
  marginal bindings; they are the largest policy-driven gaps anywhere in this document.
* **The dependency is strict and one-directional.** E-2 is worthless without E-1's masks and RHS
  machinery, and E-2 reuses them entirely — which is precisely why the owner ordered them settled
  together, and why the implementation card sequences them as one lane with two arms.

### 6.3 The design, if built

Structurally **identical to §3.1** — same K-row generalization, same two masks, same per-row RHS and
ACP — with three differences:

1. **A second, independent row family**, not a widened RPS row. The renewable row keeps its
   wind+solar eligibility (`_build_rps_row`'s CX-6a docstring reasoning is correct and untouched:
   folding nuclear into the *renewable* row would crush the REC dual). A state with both tiers gets
   **two rows** — MN's 55 %-renewable *and* MN's 100 %-carbon-free — which is what the statute says.
2. **The qualifying set is data, not a hardcoded class tuple** (rule 18's spirit, as the prompt
   requires). Each row carries a per-statute eligible-fuel set resolved against `FUEL_TYPE_MAP`,
   because the statutes genuinely differ: MN's carbon-free definition includes **hydrogen and
   biomass**; MI's clean definition admits **qualified CCS gas**. Encoding either as
   `("nuclear","hydro","wind","solar")` in code would be wrong for both and would silently mis-state
   a CCS retrofit's value in the one ISO where the retrofit screen is live.
3. **The dual's consumers grow.** A clean row's dual is an attribute price for **nuclear and hydro**,
   which today receive none from any LP row. That triggers the §6.4 no-stack requirement.

### 6.4 Rule 19 for E-2 — what already pays a nuclear or hydro MWh

This is the harder enumeration, and it is the reason E-2 needs an explicit design rather than a
row.

| mechanism | pays | exclusion |
|---|---|---|
| `eac_price_nuclear` (ZEC/CES) | nuclear, exogenous $/MWh | **The direct collision.** The `max(eac, rps_shadow)` doctrine already exists but **has never had to cover nuclear**, because nuclear is not in the renewable row. The clean row's dual must enter that same `max()` for nuclear and hydro — never a sum. |
| `federal_ces_*` premium | all clean fuels at their credit fraction | Same `max()`. And `federal_ces_replaces_state_rps` must suppress the **state clean rows too**, or the pure-federal counterfactual stops being pure. |
| **IRA §45U existing-nuclear PTC** (`policy/ira.py`) | nuclear, in the **retirement screen's revenue** | Not a dispatch adder, so no dispatch double-count — but the retirement screen would see **both** §45U and the clean dual. §45U's own gross-receipts phase-down (§45U(b)(2)) already reduces the credit as revenue rises, so the correct composition is phase-down-then-add, not `max()`. **This is a genuine open design question and it is called out, not resolved here.** |
| The renewable RPS row | wind/solar only | A wind MWh could satisfy **both** its state's renewable row and its state's clean row. **That is correct and is what the statutes say** — MN's 55 % renewable and 80 % carbon-free are separate obligations that the same MWh helps meet. Two constraints, one MWh, two duals; the *revenue* stack is the real market's (a REC and a CFE attribute are distinct products), but the model's one-certificate-sold-once doctrine means the generator's credit must be `max()`, not the sum. **Stated explicitly because it is the least obvious case and the easiest to get wrong in either direction.** |

---

## 7. Per-ISO scope for the first implementation (rule 25)

| ISO | E-1 | E-2 | why |
|---|---|---|---|
| **MISO** | **IN SCOPE** | **IN SCOPE (West, East)** | Zones are exact state unions; REC eligibility is genuinely restricted (MCL 460.1029); the reconciliation is verified and on hand; the effect is measured at +24.7 pp (E-1) and +22 to +33 pp (E-2). |
| **PJM** | **OUT — refused on structure** | out | Footprint-wide REC market ⇒ the ISO-wide row is **exact**; and its zones cut PA three ways / OH two ways, so a zonal row maps to no compliance region. Neither the trajectories nor the state-load splits are on disk. |
| **NEISO** | **OUT — refused on structure** | out | ISO-NE-wide eligibility (225 CMR 14.05) ⇒ ISO-wide row exact. Its actual defect is §8's level/tier error. |
| **NYISO** | **n/a** — one state | out | NYCA-wide eligibility ⇒ ISO-wide row exact. Its actual defect is §8. |
| **CAISO** | **n/a** — one obligated state | out | Its actual defect is §8. |
| **ERCOT** | **n/a** | n/a | No row is built. |

**Rule 25 discipline, stated for the record:** MISO's evidence charters MISO. No level, mask or split
derived here may cross into another ISO; the refusals above are derived from **each ISO's own**
statutory eligibility geography, not from MISO's result.

---

## 8. The cross-cutting defect this lane found (larger than either E-1 or E-2)

Not chartered, but it is in the same constant, it is what actually ails three ISOs, and leaving it
unstated would be the dishonest part.

### 8.1 Three rows encode a clean tier on a renewable-only row

* **NYISO** `2040: 1.00` — the CLCPA's **100 % zero-emission** standard (PSL §66-p), which counts
  nuclear and hydro. Its *renewable* target is 70 % by 2030. Applied to a wind+solar row, it demands
  that wind and solar alone cover 100 % of NY load.
* **NEISO** `.30/.45/.70/.80` — self-described in code as *"MA Clean Energy Standard + regional state
  CES blend"*. The MA **CES** (225 CMR 25.00) is nuclear-counting; MA **Class I** is the renewable
  tier and is a different, much lower number.
* **CAISO** `2040: 0.80 / 2045: 1.00` — SB 100's **zero-carbon** path. Its `.50/.60` knots for
  2026/2030 *are* the RPS (§399.15(b)(2)(B)) — so the trajectory **switches tier mid-flight**.

### 8.2 And the eligible set is narrower than the statutes' — measured

Share of 2023 ISO load, eGRID 2023, front-of-meter:

| ISO | model's row counts (W+S) | statute also counts | statutory-eligible share | **under-count** |
|---|---|---|---|---|
| **NYISO** | 0.0464 | existing hydro (counts toward the CLCPA 70 %), biomass | **0.2481** | **20.2 pp** |
| **CAISO** | 0.2542 | geothermal, biomass, small hydro ≤30 MW (RPS-eligible) | **0.3251** | **7.1 pp** |
| NEISO | 0.0628 | some biomass; MA Class I excludes existing large hydro | 0.1004 | 3.8 pp |
| PJM | 0.0546 | small biomass/landfill/hydro | 0.0652 | 1.1 pp |
| MISO | 0.1583 | small biomass/hydro | 0.1761 | 1.8 pp |

PJM's and MISO's conventions are sound — the code comment's *"the tiers' small biomass/landfill/hydro
share is folded in"* is accurate to within ~2 pp. **NYISO's and CAISO's are not.**

### 8.3 Why this outranks E-1 and E-2 in the forecast lane

The ACP escape keeps the LP feasible, so nothing crashes — the row simply **pins its dual at the ACP
ceiling for the entire horizon** (NYISO $40, CAISO $50, NEISO $50). That dual is `rps_shadow_price`,
credited to **every** new VRE candidate in `apply_economic_new_entry` (`new_entry.py:935, 1111`) and
in the retirement screen (`retirements.py:1961`). **The result is a permanent, mechanism-generated
$40–50/MWh entry subsidy in three of six ISOs, with no statute behind it.** It is cheaper to fix than
either E-1 or E-2 (a constant edit plus an eligible-set widening), more certain (the statutes are
unambiguous), and larger in effect. **Recommended as the first arm of the implementation lane.**

---

## 9. RIDER — the FFR-5B §5.4 residual, sized

**What it is.** Realized VRE commercial operation minus the vintage-gated construction-committed
(`U/V/TS`) pipeline MW the FFR-5E channel would inject, per ISO-year — the named size of the
corporate-PPA / beyond-horizon procurement FFR-5B disclosed as having **no admissible
representation**. **It feeds no mechanism.**

**Method (committed artifacts only, read-only).** Realized COD from the canonical
`data/raw/eia-860/eia860_generator_operable.parquet`, joined to `eia860_plant.parquet` for the
balancing authority and mapped through the repo's own `BA_CODE_TO_ISO` — the identical join
`load_planned_additions` performs (`eia860.py:2045–2049`). Pipeline from
`vintage_<V>/eia860_generator_proposed.parquet` at status ∈ {U, V, TS} with `Effective Year > V`.
Horizon *h* means the run's vintage is *V = Y − h*. **The operable sheet is read here and only here:
FFR-5B §3.1 forbids importing it into the procurement *path*, not into a design-time measurement, and
this is a sizing of a disclosed limitation rather than a model input.**

**Cross-check that it measures the same object as FFR-5B:** realized MISO **solar** COD 2021–2025
totals **18,649 MW** — FFR-5B's 18.649 GW figure, reproduced independently.

### 9.1 Residual MW by ISO-year, `U/V/TS` basis, *h*=1 (the channel's most favourable horizon)

| ISO | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| CAISO | 1,161 | 1,317 | 462 | 185 | 1,314 | 2,362 | 1,028 |
| ERCOT | 2,199 | **−734** | 3,001 | 1,267 | 1,477 | 2,625 | 4,860 |
| MISO | 1,345 | 1,145 | 1,914 | 1,217 | 1,102 | 2,246 | 4,648 |
| NEISO | 242 | 25 | 227 | 329 | 236 | 45 | 252 |
| NYISO | 209 | **−461** | 265 | 142 | 697 | 859 | 282 |
| PJM | 586 | 1,559 | 1,900 | 278 | 2,157 | 2,598 | 943 |

*(wind + solar, MW. Negative = the committed pipeline for that year exceeded realized COD — projects
slipped past their filed effective year. Only two cells in seven years, both 2020.)*

### 9.2 Cumulative 2021–2025 and coverage

| ISO | realized MW | pipeline *h*=1 | **residual *h*=1** | coverage *h*=1 | pipeline *h*=2 | **residual *h*=2** | coverage *h*=2 |
|---|---|---|---|---|---|---|---|
| CAISO | 11,202 | 5,851 | **5,352** | 0.52 | 1,554 | 9,649 | 0.14 |
| ERCOT | 37,743 | 24,514 | **13,230** | 0.65 | 5,837 | 31,906 | 0.15 |
| **MISO** | 25,849 | 14,722 | **11,127** | 0.57 | 2,236 | 23,613 | 0.09 |
| NEISO | 2,172 | 1,083 | **1,089** | 0.50 | 89 | 2,082 | 0.04 |
| NYISO | 3,088 | 842 | **2,245** | 0.27 | 233 | 2,854 | 0.08 |
| PJM | 14,686 | 6,809 | **7,877** | 0.46 | 1,116 | 13,570 | 0.08 |

### 9.3 Reading it

* **The residual is large everywhere, and it is smallest at *h*=1.** Even at the one-year horizon
  where the pipeline is most informative, **35–73 % of realized VRE build has no admissible
  representation** in the FFR-5E channel. At *h*=2 that rises to **85–96 %**, because a project
  commissioning in *V+2* frequently had not reached committed status — or the sheet at all — at
  vintage *V*.
* **It confirms FFR-5B's pre-registration quantitatively.** A 2021–2025 MISO hindcast at vintage
  2020 is *allowed to see* the *h*=5 pipeline, which is far thinner than even the *h*=2 column here.
  **The channel is arithmetically incapable of closing this, and that is the information gate
  working.**
* **It is an upper bound on the corporate-PPA share, not an estimate of it.** The residual also
  contains projects that entered the sheet after *V*, status regressions, and (in ERCOT/MISO)
  merchant build that no procurement instrument would ever have covered. Decomposing it further
  would require exactly the proprietary series rule 13 excludes. **Its honest use is as the size of
  the disclosed limitation — the number to quote when saying "this is not represented" — never as a
  target to close.**

---

## 10. Reproduction

Design-time measurements only; all read committed on-disk data and shipped code, none touches the
solve path. Scratch scripts (session scratchpad, not committed):

* `e1_zonal.py` — per-zone / per-state generation by fuel and shares of zone load (§2.2, §3.1's
  0.0002–2.80 range, §8.2), via `zone_assignment.assign_zone` on eGRID `PLNT23` ORIS codes.
* `e1_bind.py` — the E-1 binding table (§2.2), the §1.5 blend reproduction, the E-2 clean-tier table
  (§6.2) and the eligible-set screen (§8.2).
* `rider_residual.py` / `rider_table.py` — §9.

Sources: `data/raw/fleet-egrid/egrid2023_data_rev2.xlsx` (PLNT23); `data/raw/{MISO,PJM,ISNE,NYIS,
CISO,ERCO}_region.parquet` (EIA-930 hourly demand, 2023); `data/raw/eia-860/vintage_{2018..2024}/`
+ the canonical operable/plant sheets; `config/capacity_market.py::STATE_RPS_FLOORS`/`STATE_RPS_ACP`;
`config/iso_configs.py`; `data/zone_assignment.py`; `model/lp/rows.py`, `layout.py`, `model.py`;
`policy/{rps,eac,federal_ces,ira}.py`; `model/capacity_evolution/{new_entry,retirements}.py`.

Statutory sources cited in §3.4, §6.1 and §8.1: Minn. Stat. §216B.1691 (2023 HF7); 2023 PA 235
(MI SB 271), MCL 460.1028/460.1029; P.A. 102-0662 (IL CEJA); N.J.A.C. 14:8-2.3; Md. Code Pub. Util.
§7-701 *et seq.*; 225 CMR 14.05 and 225 CMR 25.00 (MA); NY PSL §66-p (CLCPA); Cal. Pub. Util. Code
§399.15(b)(2)(B) (SB 100); 26 U.S.C. §45U.

---

## 11. What I did NOT decide

* **I did not open the implementation.** No code, no schema, no `ScenarioConfig` field, no matrix
  cell, no test. §12 is a proposed card, not a charter.
* **I did not solve, score, register or touch any year.** Nothing on any dashboard changed; rule 15
  does not apply (no run was produced). The holdout freeze was never approached.
* **Rule 28 discharge: NO matrix cell was changed and no row was minted.** A design lane adjudicates,
  tests and arms nothing. The RPS row is LP-native and carries no matrix row today; the
  implementation PR that creates the gate flags mints their rows, per duty 28(c). Recorded here so
  the duty is not lost.
* **Rule 24 discharge: nothing to register.** §12 names the *entire* prospective tunable surface (two
  gate flags, plus statutory levels that live in `constants`-style tables with citations) so a future
  implementation cannot expand it without the expansion being visible against this document.
* **I did not decide the §6.4 §45U composition question.** Whether a state clean-row dual composes
  with the §45U existing-nuclear PTC by `max()`, by phase-down-then-add, or by something else is a
  real open design question with a revenue consequence for every nuclear unit in MISO-West and
  MISO-East. It is named, not answered, and it blocks E-2's *arming* — not its implementation.
* **I did not resolve the ND/SD/MT split of MISO-West** (§1.4). It is bounded at ±0.0345 on one
  zone's target and is one EIA-861 line to close.
* **I did not verify PJM's or NEISO's per-state trajectories.** §1.3 records that they are absent
  from the repo and their sources are not on disk; since §7 refuses both ISOs on structure, deriving
  them would have been work in service of a design I am recommending against.
* **I did not re-open the ISO-wide row's *level* for PJM or MISO.** The §1.5 reproduction says the
  shipped blend is arithmetically sound; the defect is where compliance may be sourced, not how much
  is owed.
* **I did not fix the stale `runner.py:2036-2039` / `federal_ces.py:466` "PJM carries no RPS row"
  comment** (§5.4) — design-only lane; flagged for the implementation PR.
* **I did not size §8's entry-subsidy consequence in MW or $.** That needs a solve, and this lane
  runs none. The mechanism is demonstrated from the code path; its magnitude is an open measurement.

---

## 12. PROPOSED OWNER CARD — for the manager to put

```
### CARD D-19 — The RPS row: fix the tier/eligibility level first, then the compliance grain?

**Measured (FFR-6B, docs/handoffs/ffr-6b-rps-grain-clean-tiers-2026-08-05.md).** Three findings, and
the ordering is the decision.

(i) E-1's DIAGNOSIS NEEDS ONE CORRECTION. The defect is not that the row is ISO-wide — it is that
one ISO-wide row silently asserts FREE INTRA-ISO REC TRADE, which is TRUE in four ISOs and FALSE in
MISO. PJM Class I RECs trade footprint-wide (the PJM Tri/Quad-Qualified products; N.J.A.C. 14:8-2.3
admits units "located within the PJM region"); MA Class I qualifies the ISO-NE Control Area (225 CMR
14.05); NY Tier 1 is the NYCA; CAISO is one obligated state. For those four the single row is
ARITHMETICALLY EXACT, not a dilution. MISO is the exception: Michigan's credits must come from
systems "located within this state" (MCL 460.1029, MIRECS). MEASURED at MISO zone grain (which is an
exact union of whole states): MISO-East owes 0.328 of zone load against 0.081 measured VRE — a
24.7 pp deficit on 24% of ISO load — while MISO-Plains runs a 41.5 pp SURPLUS against a 0.064
obligation, and the ISO-wide row sees 0.158 against 0.160 and is satisfied to 0.2 pp. IOWA'S SURPLUS
IS PAYING MICHIGAN'S BILL, WHICH MICHIGAN'S STATUTE FORBIDS. FFR-5B's claim that the reconciliation
is already derived VERIFIES FOR MISO (and re-blending its own parts reproduces the shipped knots:
0.1139/0.1606/0.1981 vs 0.11/0.16/0.20) and FAILS for PJM and NEISO, whose per-state trajectories and
state-load splits are neither in the repo nor on disk.

(ii) E-2 IS ADJUDICATED — IT BINDS, AND ONLY AT E-1's GRAIN. ISO-wide, MISO's clean generation is
0.320 of load against a 0.091/0.212/0.251 obligation (2030/35/40): SLACK EVERY YEAR — FFR-5B's
"maybe it's just slack" hypothesis is CONFIRMED for the ISO-wide form. At state-group grain
MISO-West is short 14.0 pp by 2030 rising to 29.4 pp by 2040 (MN 80/90/100% carbon-free, Minn. Stat.
§216B.1691 subd. 2g) and MISO-East short 21.7 pp by 2035 rising to 33.1 pp by 2040 (MI 80%/100%,
2023 PA 235). Illinois is a NULL and is recorded as one: CEJA's 100%-by-2050 is a state policy goal
plus source-side emission phase-outs, NOT an LSE share obligation, so it gets no row.

(iii) A THIRD DEFECT, NOT CHARTERED, THAT OUTRANKS BOTH. Three of the five RPS-carrying ISOs encode a
CLEAN (nuclear/hydro-counting) target on the RENEWABLE-ONLY (wind+solar) row — NYISO's 2040:1.00 is
the CLCPA zero-emission standard, NEISO's trajectory is self-described in code as a "CES blend",
CAISO's 2040:0.80/2045:1.00 is SB 100's zero-carbon path — and the eligible set omits generation the
statutes count: NYISO by 20.2 pp (existing hydro counts toward the CLCPA 70%), CAISO by 7.1 pp
(geothermal, biomass, small hydro). The ACP keeps the LP feasible, so the visible symptom is that
those rows' duals PIN AT THE ACP CEILING FOR THE WHOLE HORIZON — and that dual is rps_shadow_price,
credited to every new VRE candidate in apply_economic_new_entry. A PERMANENT $40-50/MWh ENTRY SUBSIDY
IN THREE ISOs WITH NO STATUTE BEHIND IT. Cheaper to fix, more certain, and larger than (i) or (ii).

**Recommendation — (a) CHARTER ONE LANE, THREE ARMS, IN THIS ORDER.**
  ARM 1 (do first, alone if budget is tight): fix the tier/eligible-set level in NYISO, NEISO and
  CAISO. A cited constant correction plus a statute-defined eligible-fuel set. No new row, no new
  grain, no new gate flag. This is a rule-14 [R-ACCURATE] input correction and it removes a
  mechanism-generated subsidy.
  ARM 2: generalize _build_rps_row to K rows, each with (obligated_zones, eligible_zones, RHS, ACP).
  Today's behaviour is the K=1, mask=all special case, so FOUR ISOs stay BYTE-IDENTICAL by
  construction. Arm MISO only (rule 25). Required companion: rps_shadow_price becomes PER-ZONE at its
  three consumers — a scalar left in place would broadcast MISO-East's dual to an Arkansas candidate
  and rebuild the very defect the row fixed.
  ARM 3: the clean-tier row family, reusing Arm 2's machinery, MISO-West and MISO-East only.
  ZERO FREE PARAMETERS ACROSS ALL THREE ARMS. Entire tunable surface: two gate flags
  (default OFF, forecast-mode only) plus statutory levels in cited tables. Matrix rows minted in the
  same PR (rule 28c).

**Option (b), do E-1 first and skip Arm 1 — I think this is wrong.** It is the natural reading of
FFR-5B's escalation and it leaves the largest defect in place while doing the hardest work.

**Option (c), zonal rows everywhere — I think this is wrong and it would be a regression.** PJM's
zones split Pennsylvania THREE ways and Ohio two (zone_assignment._pjm_zone's lat/lon rules), so a
PJM zonal row corresponds to no compliance region at all and would give one state three REC prices.
Measured in-zone VRE/load ranges from 0.0002 (NYC) to 2.80 (CAISO SP15_rest): generation sits where
the resource is, load where the people are, and no US RPS requires them to match. "One row per zone"
is the wrong instrument; "one row per compliance region" is the right one, and in four ISOs that
region IS the ISO.

**Option (d), do nothing — I think this is wrong.** MISO-East's 24.7 pp deficit and MISO-West's
29.4 pp clean deficit are the two largest policy drivers in the model's largest ISO, and both are
currently invisible.

**CARRIED FORWARD, so it is not lost:** the §45U-vs-clean-dual composition for nuclear (max()?
phase-down-then-add?) is OPEN and blocks ARM 3's ARMING, not its implementation. E-1 MUST NEVER
ACQUIRE A BUILD LIMB — the row's only legitimate output is a price; a force-build limb would stack
against FFR-5E's procurement channel and is the rule-19 failure FFR-5B already refused.

**RIDER DELIVERED (FFR-5B §5.4 residual, sized, feeds no mechanism):** 2021-2025 cumulative VRE build
with NO admissible representation, at the channel's own U/V/TS basis and its best horizon (h=1) —
ERCOT 13.2 GW, MISO 11.1 GW, PJM 7.9 GW, CAISO 5.4 GW, NYISO 2.2 GW, NEISO 1.1 GW (35-73% of realized
build; 85-96% at h=2). Method reproduces FFR-5B's MISO figure exactly (18,649 MW solar 2021-25). It
is an UPPER BOUND on the corporate-PPA share and the number to quote when saying "not represented" —
never a target to close.

**Sign-off D-19:** ☐ (a) one lane, three arms, in order   ☐ (b) E-1 first, skip Arm 1
☐ (c) zonal rows everywhere   ☐ (d) no action   ☐ other: ____________
owner: ________  date: ____
```
