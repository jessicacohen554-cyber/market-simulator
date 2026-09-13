# NWPP Addition Desk — ledger (2026-09)

The live record of the NWPP addition program. **This ledger wins where it and
`docs/multi-iso/nwpp-addition-plan-2026-09.md` diverge on live state**; the plan owns the charters
(§8) and the decisions (§3), this owns who is running what.

Refresh discipline: one refresh = one §0 entry = one ledger commit = one small PR, off a branch
recreated fresh from `origin/main`.

---

## 0. Live state — newest entry FIRST

### r#1 — 2026-09-13 — SITTING #1: cards N1, N2, N3 RULED (main `2c2fc065`)

**What happened.** The three sitting-#1 cards were served as clickable decision cards. **N1 and N2 were
ruled as the desk recommended. N3 was ruled AGAINST the desk's recommendation**, and that one ruling
restructures the program.

| Card | Ruling | vs. desk |
|---|---|---|
| **N1** | **All 17 BAs**, key `NWPP`; NEVP in, Canada out, AVRN/GRID supply-side only | as recommended |
| **N2** | **Both (a) and (b)** — charter NWPP-13's STOP-gated WEIM build **and** rule now that a failed gate yields a determination naming its own basis, never a bare `CALIBRATED` | as recommended |
| **N3** | **BUILD CASCADE COUPLING FIRST** — hydraulic coupling of the Columbia mainstem is built **before** any first keeper | **AGAINST**: the desk recommended proceeding on the monthly-budget machinery with the gap declared |

**What N3 changes, implemented in the plan rather than noted.** The desk's recommendation would have
pre-declared cascade coupling as W5 lever NWPP-54 and solved a first keeper without it. The owner ruled
that the first NWPP number must mean more than a test of monthly hydro budgets. So:

- A new wave **W3b** is inserted between derivation and the first solve, and **W4 does not start without
  it** (plan §4).
- A new lane **NWPP-36** `[FABLE]` is added to the lane table (plan §5) and its W3 delta written (§8).
- **Lever NWPP-54 is RETIRED from the W5 queue**, its content promoted into NWPP-36. The queue is now
  NWPP-55/56/57/58/59.
- **Gate G8 is AMENDED** (plan §7). This is the part that mattered and the desk checked it rather than
  assuming: G8 forbade *any* new `ScenarioConfig` field through W4, and a mechanism is a field — so the
  ruling and the gate were in direct tension. **The tension resolves by construction, not by exception.**
  The repo carries `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`, and a field
  registered default-OFF in both, in the same commit, is dropped from the hash at its default so every
  pre-existing cached run — every ISO's keepers included — keeps its key. **There is a worked hydro
  precedent to copy rather than invent:** `hydro_budget_period_by_instrument` (lane nyiso-220) is the
  **first entry** in that tuple and was added on exactly this basis. NWPP-20 remains forbidden any field
  at all; the exception is NWPP-36's single field and nothing else.

**What did NOT change.** N3 is a sequencing and scope ruling, not a licence: rule 1 `[R-STRUCT]` still
forbids judging the coupling by whether it improves a residual — and since no NWPP run exists, there is
no residual to judge it against, which is the cleanest possible position for a structural build. Rule 2
`[R-VECTOR]` binds its LP rows. Rule 28 `[R-MECH-MATRIX]` (c) requires its matrix base row plus one `·`
cell per foreign shard in the same PR.

**The joint-sitting option on N2 was offered and NOT taken.** The desk presented "rule N2 and SOCO's S2
together" as an explicit option; the owner ruled N2 on its own. **R-c therefore stays OPEN and must be
surfaced at every sitting that touches scoring** — the SOCO desk's ledger still routes that the rubric
question be ruled once for both, and it now has one half-answer. That is a live divergence risk, not a
closed item.

**Gates run:** none — this refresh touches only the three program documents plus the two index rows, so
every gate's input is unchanged. Recorded UNREAD rather than carried forward green.

**Next act:** issue W1 — NWPP-10, NWPP-11, NWPP-12 (all `[OPUS]`, `DATA PROFILE: shared`, parallel,
file-disjoint) **and NWPP-13** `[FABLE]`, which N2's ruling unblocks. Then sitting #2 for N4–N8 and N10
once W1's evidence lands. NWPP-36 is chartered at the sitting that follows NWPP-32.

---

### r#0 — 2026-09-13 — CHARTER (main `2c2fc065`)

**What happened.** The owner directed a chartering session for adding the Northwest Power Pool /
Western Power Pool footprint as a registered region, using the SPP addition workstream as the process
reference and the SOCO charter (2026-09-12) as the non-market precedent. The session measured its
facts rather than restating the ones it was handed, and four of those measurements changed the
program's shape (see **Corrections** below).

**Committed at charter:** `docs/multi-iso/nwpp-addition-plan-2026-09.md`,
`docs/handoffs/nwpp-desk-handoff-2026-09-13.md`, this ledger, plus one row in
`docs/multi-iso/README.md` and one `CHANGELOG.md` entry. Nothing else. No code, no data, no registry
touched.

**Measured in the charter session** (plan §2 carries all of it with its provenance; do not
re-derive):

| Fact | Value |
|---|---|
| Hermiston | EIA plant **54761**, Umatilla County OR, 621.2 MW / 4 CC gens, op. 1996, BA **PACW**, NERC WECC. The adjacent Hermiston Power Partnership is plant **55328**, 689.4 MW, BA **GRID** |
| Fleet, 17 candidate BAs, EIA-860 operable | **940 plants** (1,082 plant-table rows) · **1,932 generators** · **98,738.1 MW** |
| NERC | WECC 98,238.1 / 1,930 gens · **TRE 500.0 / 2 gens — a source defect, NWPP-10 adjudicates** |
| By technology | hydro **35,799.5 (36.3 %)** · CC 15,609.3 · wind 14,460.3 · solar 10,049.9 · coal 8,910.2 · CT 4,565.5 · batteries 2,522.0 · gas ST 2,163.0 · **nuclear 1,200.0** · geothermal 972.6 · **pumped storage 314.0** |
| Hydro concentration | 288 plants; **8 plants ≥ 1 GW = 17,821.8 MW (49.8 % of all hydro)**; 141 plants < 10 MW = 504.1 MW (1.4 %) |
| Ownership | **Electric Utility 68,860.0 MW (69.7 %)** · IPP Non-CHP 26,962.3 · IPP CHP 1,568.8 |
| Demand (EIA-930, committed) | **283.97 / 291.56 / 294.86 TWh** (2023/24/25) |
| Coincident peak, defect-screened | **49,290 / 52,564 / 50,953 MW**; load factor 0.658 / 0.631 / 0.657 |
| 2024 load share | BPAT 20.26 · PACE 18.10 · NEVP 14.11 · PSEI 8.53 · PGE 7.79 · PACW 7.30 · IPCO 6.43 · AVA 4.44 · NWMT 4.18 · SCL 3.23 · GCPD 2.29 · TPWR 1.56 · DOPD 0.82 · CHPD 0.68 · WAUW 0.28 · **AVRN 0.00 · GRID 0.00** |
| Timezones | EIA-930 assigns **one zone per BA**: Mountain = NWMT, PACE, WAUW; Pacific = the other 14 (incl. IPCO) |
| CAMPD CEMS | present MT/NV/WY/CA; **ABSENT ID/OR/UT/WA** (and CO) |
| Probes at this pin | EPA CAMPD bulk **206** anon · CAISO OASIS `ATL_APNODE` **200** and `PRC_RTPD_LMP` **200 with real 15-min LMPs** · EIA ICE workbooks **200** · BPA `baltwg.txt` **206** · westernpowerpool.org **200** · wecc.org **200** · PUDL FERC-714 **200** · `ferc.gov` **403** · no `EIA_API_KEY` |

**Corrections and extensions to the facts this desk was handed** — recorded here because a desk that
silently absorbs a wrong premise mis-charters every lane downstream:

| # | Handed | Measured | Consequence |
|---|---|---|---|
| 1 | *"EIA-930 hourly parquets on disk: … NOT ONE NWPP BA. Every one must be fetched."* | The **derived** per-BA files are indeed absent, but `data/raw/eia-930/EIA930_BALANCE_<yr>_<half>.parquet` is **committed 2019-01 → 2026-06 and carries all 17 BAs** with Demand, Net Generation, Total Interchange, Sum(Valid DIBAs), Adjusted demand and **both** time columns | NWPP-11's load spine is a **DERIVE, not a fetch**, and needs no `EIA_API_KEY`. Manifest row 2 rewritten |
| 2 | *"940 plants / 98,738.1 MW"* | MW confirmed **exactly**; 940 is the count of plants **with ≥ 1 operable generator** — 1,082 plant-table rows carry a footprint BA | stated precisely in plan §2.1 so NWPP-10's census reconciles |
| 3 | (not handed) | **AVRN and GRID carry NULL demand in all 26,295 hours** — generation-only BAs holding 3,538.1 MW | they are supply-side members and **not zone candidates**; card N5's grouping must place their generation |
| 4 | *"the two-timezone problem"* (SOCO gate G19) | **Largely closed by measurement**: 14 Pacific / 3 Mountain, one zone per BA, both time columns committed | card N6 is reduced to a canonical-convention choice, not a data problem |

**Additional measured findings with no handed counterpart:** 30 defective demand hours of 394,424
(AVA 810,948 MW at 2025-10-12 10:00 UTC; −58,286 at 2024-01-05 16:00; NWMT 11, NEVP 6, PACE 1,
SCL 2) which unscreened put the 2025 coincident peak at 835,464 MW — and the `Demand (MW) (Adjusted)`
column already carries the screened series. The **data-profile token trap is the worst yet measured**:
`ava` steals ten files across five ISOs, `grid` steals `fleet-egrid`, `pge` steals CAISO's
`reference/pge-helms-ps-plant-2008`, `wpp` steals SPP's `SWPP_*`. And
`data/raw/eia-860/eia860_generators.parquet` is a **curated seven-ISO file with zero NWPP rows**.

**The program's defining problem, stated at charter so it is never discovered late:** the Northwest
Power Pool publishes **no LMP** and had **no day-ahead market** in 2023–2025. Unlike SOCO, two
measured public prices **do** cover it — CAISO **WEIM** 15-minute LMPs (212 `EIMT` apnodes across
this footprint's BAs; a live pull returned $63.9213/MWh) and the **Mid-C** traded index (244 trade
dates, 4,748,000 MWh in 2023). Neither is straightforwardly the benchmark: WEIM clears **imbalance
only** and its share of footprint volume is `pending NWPP-13`; Mid-C is **daily and peak-only**, so
it can anchor a level and score nothing. Card **N2** is the only route, and it is due at **sitting
#1**.

**Gates run at charter:** none — the charter commit touches no code, no data and no registry, so
every gate's input is unchanged. Recorded UNREAD rather than carried forward green.

**Next act:** sitting #1 — serve cards **N1** (the region and its footprint), **N2** (the price
benchmark / rubric class) and **N3** (hydro representation) to the owner via AskUserQuestion, then
issue W1 (NWPP-10/11/12; NWPP-13 only if N2 rules for option (a)).

---

## 1. Scoreboard

| Lane | Model | Wave | Status | Branch | FINDING |
|---|---|---|---|---|---|
| NWPP-10 audit | OPUS | W1 | **ISSUABLE** | — | — |
| NWPP-11 CEMS + 930 derive + interchange + hydro | OPUS | W1 | **ISSUABLE** | — | — |
| NWPP-12 WECC paths / WRAP / IRPs / fuel | OPUS | W1 | **ISSUABLE** | — | — |
| NWPP-13 WEIM price index | FABLE | W1 | **ISSUABLE** (card N2 ruled r#1) | — | — |
| NWPP-20 registration | FABLE | W2 | BLOCKED on N4–N8 + LTLF (N1/N3 ruled r#1) | — | — |
| NWPP-21 matrix shard | OPUS | W2 | BLOCKED on collision check | — | — |
| NWPP-30/31/33/34/35 | OPUS | W3 | BLOCKED on NWPP-20 | — | — |
| NWPP-32 hydro budget | FABLE | W3 | BLOCKED on NWPP-20 + NWPP-11 | — | — |
| NWPP-36 cascade coupling | FABLE | **W3b** | BLOCKED on NWPP-20 + NWPP-32 — **inserted by ruling N3** | — | — |
| NWPP-40 first solve | FABLE | W4 | BLOCKED on NWPP-30/31/32/33 **and NWPP-36** | — | — |
| NWPP-55…59 levers | — | W5 | pre-declared, not issuable (**NWPP-54 RETIRED into NWPP-36**, ruling N3) | — | — |
| W6 forecast entry | — | W6 | ROUTED to the capx director (card N9) | — | — |

## 2. Owner rulings — verbatim, numbered

| # | Card | Ruling | Date |
|---|---|---|---|
| O-1 | charter | Charter the NWPP addition using the SPP workstream as reference and the SOCO charter as the non-market precedent | 2026-09-13 |
| N1 | the region, key and footprint | **ALL 17 BAs** — key `NWPP`; NEVP in; Canada out; AVRN/GRID supply-side members, not zone candidates. *As the desk recommended.* | 2026-09-13 |
| N2 | price benchmark / rubric class | **BOTH (a) AND (b)** — charter NWPP-13's STOP-gated WEIM build, AND rule now that a failed gate yields a determination naming its own basis, never a bare `CALIBRATED`, with the gap at full magnitude. Neighbouring-hub substitution stays refused (G17). *As the desk recommended. The joint-sitting-with-SOCO option was offered and not taken — R-c stays open.* | 2026-09-13 |
| N3 | hydro representation | **BUILD CASCADE COUPLING FIRST** — hydraulic coupling of the Columbia mainstem is built before any first keeper. ***AGAINST the desk's recommendation***, which was to proceed on monthly budgets with the gap declared. Effects: new wave W3b, new lane NWPP-36, lever NWPP-54 retired, gate G8 amended. | 2026-09-13 |
| N4–N8, N10 | CAISO seam, topology, timezones, adequacy, CEMS scope, first-solve screen | **PENDING** — due sitting #2 | — |
| N9 | W6 routing | **PENDING** — due when a keeper exists | — |

## 3. Routed — open, not this desk's to fix

| # | Item | Owner | Why it stays visible |
|---|---|---|---|
| R-a | **The CAISO double-count.** CAISO's `WECC_import` zone is fed by firm tranche `PNW_hydro_base` (`interchange/caiso.py:443`) — this footprint, by name, as a Tier-3 contract-cost proxy. Registering NWPP puts the same energy on both sides of a seam, represented two ways | the CAISO lane (rule 25 `[R-ISO-SCOPE]`) | Card N4 governs NWPP's side only; the exposure does not disappear by being unmentioned |
| R-b | The rubric cannot express a determination for a region whose only price is an imbalance price covering an unmeasured share of volume | the owner (card N2) | A keeper solved before it is ruled cannot be scored |
| R-c | **The SOCO program shares R-b in a harder form** (no price at all), and its ledger §3 R-b already routes *"the owner should rule the rubric question ONCE, for both"* | the owner | Two desks asking the same question twice invites two different answers. **STATUS AFTER r#1: the joint sitting was offered as an explicit option and NOT taken — N2 is ruled for NWPP alone.** So the two programs now hold one half-answer between them and the divergence risk is live, not hypothetical. Surface at every sitting that touches scoring; **do not answer card S2 and do not present a joint ruling** |
| R-d | 500.0 MW filed under BA `DOPD` with state `TX` / NERC `TRE` | NWPP-10 adjudicates; any upstream EIA correction is outside this program | A silent mis-key would put 500 MW of the wrong interconnection in the fleet |
| R-e | `data/fleet/models.py:221` inverts `BA_CODE_TO_ISO` with a comprehension that **silently keeps only the last BA per ISO**. Every existing entry is 1:1; NWPP's is **17:1** | NWPP-20 audits it | The single most likely silent bug in the registration |

## 4. Collision register

| # | Surface | Other writer | Action |
|---|---|---|---|
| C-1 | `config/capacity_market.py`, `config/constants.py`, `model/interchange/spec.py` | capx D-lanes, the SCN desk, the per-ISO calibration lanes, **and the SOCO desk** | NWPP-20 rebases last and appends; the desk re-checks their ledgers' top entries at issuance |
| C-2 | `docs/codebase-site/data/mechanism-matrix.js` (base file), `scripts/lib/mech_matrix.py` | every ISO's lanes; **SOCO-21 is chartered to add a shard to the same file** | NWPP-21 is issued only after the desk verifies nobody is mid-edit, and re-counts `isos` at its own sha |
| C-3 | **The pin list itself** — `_ISO_BUILDERS`, `SURFACE_ISOS`, `_MULTI_YEAR_ISOS`, `ISO_ORDER`, `data-profiles.yaml`, `calibration-solve.yml` | **the SOCO desk's NWPP-20 analogue, SOCO-20** | Whichever lands second re-counts (plan §0). Neither plan's §2.3 may be executed from its own number |
| C-4 | `docs/multi-iso/00-iso-addition-protocol.md` §0/§3 (the registered-region count sentence) | SOCO-10 is chartered to edit the same sentence | NWPP-10 reads it at its own base sha and edits what it finds, never what the charter says it says |

## 5. Issuance record

| Sitting | Date | Lanes issued | Cards served |
|---|---|---|---|
| r#0 | 2026-09-13 | none (charter commit) | N1, N2, N3 served to the owner at the close of the charter session |
| r#1 | 2026-09-13 | none yet — W1 (NWPP-10/11/12/13) is the next act | N1, N2, N3 **RULED**; N3 against the desk's recommendation |

## 6. Errors against interest

*(The desk records its own mistakes here, in its own words, so the next refresh does not repeat
them.)*

- **E-1 (r#0, caught in-session).** The desk's first census script joined the plant and generator
  frames without disambiguating the `State` column present in both, and the groupby raised
  `KeyError: 'State'`. Nothing downstream consumed the bad frame, but the lesson stands for every
  lane: the EIA-860 plant and generator parquets share several column names, and a merge that does
  not name its suffixes will silently take the wrong one where it does not raise. NWPP-10's census
  should state which frame each column came from.
- **E-2 (r#0, method note against interest).** The desk accepted the handed probe results as a
  starting point but re-ran every one at its own pin rather than citing 2026-09-12 results as
  current. Two differed in form (EPA and BPA answered 206 to a range request rather than 200), which
  changes nothing — but had a host gone dark overnight, a carried-forward green would have sent a
  lane at a dead route. No lane should cite a probe it did not run.
