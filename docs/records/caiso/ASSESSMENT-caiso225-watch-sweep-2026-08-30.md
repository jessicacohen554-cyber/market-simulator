# ASSESSMENT — caiso-225: THE POST-caiso-224 WATCH SWEEP — every armed watch item re-tested and NULL: W-1 (PATH15_BG/PATH26_BG still ERR 1000; TI universe still zero-internal — 58 = caiso-218's 56 + SunZia + Pinal Central, both new *boundary* interties), W-2 (constraint family still shadow-price-only on live columns; spec still the Fall-2017 v5.1.x family; the corridor causes still present), W-3 (TWO new DMM documents tested — Q4-2025 of 2026-03-31 and the 2025 ANNUAL of 2026-06-26 — and NEITHER prints element limit MW; the 2023 annual stays the only MW vintage), and the caiso-224 F2 derate WATCH null (TRNS_OUTAGE still boundary-only; the 7-day/1000-day transmission outage reports are certificate-walled and forward-only; Order 881 AARs participant-facing, effective ≤ 2026-12-01 — the one DATED future event most likely to move W-1/W-2). The caiso-131 A3 SoCalGas OFO record is CONFIRMED AVAILABLE AND TRIVIALLY FEASIBLE (public Envoy event histories, High 1997–2026 / Low-EFO 2015–2026, date+stage+tolerance grain, the Jan-2023 blowout cluster present) — intake remains UNFUNDED. NOTHING FIRES; no data-intake charter opens; the frontier is re-affirmed and the caiso-222 Q1 disposition question is put back to the owner as the sole remaining route at this grain. ZERO SOLVES (2026-08-30)

**Charter.** The owner's caiso-225 handoff: the post-caiso-224 frontier check and
watch sweep — run the cheap watch tests the caiso-222 §9 rulings armed and
adjudicate what, if anything, fired. ZERO SOLVES ran; no LP, nothing armed,
nothing registered, no cell verdict moved, no `ScenarioConfig` field, no derive.
Keeper **UNCHANGED** at `2026-08-26-caiso-220-c1-crosswalk` (NOT-YET on C3a
alone, +4.0 PASS/+12.5/+15.5 %; C3c the single ledgered caveat).
`calibration-complete.json` (no CAISO marker) and `holdout-freeze.json` (ACTIVE)
untouched; every read stayed inside 2023–2025 (rule 22) — the watch tests read
*publication surfaces* (OASIS report schemas/universes, DMM report text, Envoy
event pages), never model years or actuals.

Instrument: `results/calibration/_caiso225_watch_results.json` — every measured
output of the five tests below (fetched 2026-08-30 UTC through the session
proxy). The governing records: the watch table
`ASSESSMENT-caiso222-owner-sitting-2026-08-30.md` §(i) (armed by its §9
rulings), the F2 watch `FINDING-caiso224-fsno-arm-2026-08-30.md` §D/§G, and the
A3 ask `FINDING-caiso131-tail-and-c3a-decomposition-2026-07-27.md` §6/§9.

---

## §0 — Standing state, verified

* `git ls-remote` shows no in-flight CAISO branch; main is current through the
  caiso-224 merge (PR #4415). This branch is fresh off that main.
* The caiso-224 record stands as read: the FSNO partition REPRESENTATION
  (P-A′ + caiso-223 membership + measured 3-way load split) unrefuted and
  standing; the static DMM-cap arm adjudicated **R** (F1 3/3 years on
  NP15↔FSNO, F2 static-vintage); `caiso_fsno_subzonal_topology` default-off,
  its shard cell already stamped by the finisher session. Re-arm feeds: W-2 /
  W-3 / the F2 derate watch — i.e. exactly the objects this sweep tests.

## §1 — W-1: the OASIS TI universe (branch-group re-enforcement). **NULL**

The caiso-222 §(i) trigger, verbatim: *"`ti_id=PATH15_BG`/`PATH26_BG` today
returns ERR 1000; the July-2024 FNM ITC/BG reference carries no Path 15/26
entry. Either changing is the trigger."*

* **Explicit BG queries**: `TRNS_USAGE` with `ti_id=PATH15_BG` and
  `ti_id=PATH26_BG` (trade day 2025-06-02, inside the ~39-month retention)
  both return **ERR 1000 — "No data returned for the specified selection"** —
  byte-for-byte the caiso-218 signature. Unchanged.
* **Universe census, controlled**: the same trade day caiso-218 censused
  (2025-06-02) returns **56 TI_IDs today — identical to the caiso-218 census,
  zero dropped**. A recent trade day (2026-08-25; 325,728 rows) returns
  **58**, and the two additions are `SUNZIA_ITC` and `PINALCENT500_ITC` — the
  SunZia new-build delivery and the Pinal Central 500 kV Arizona boundary
  point: **new external interties, not internal paths**. Zero `_BG`-suffix
  objects, zero internal corridor objects, in either census.

The 2018-11-01 discontinuation of the internal Path Branch Groups stands; the
route-1 "zero-new-plumbing intake path" remains closed. (The universe delta is
recorded so the next census diff is not puzzled by 56 → 58.)

## §2 — W-2: a limit/flow field in the constraint-report family. **NULL**

Live day-pull (trade day 2026-08-25) of all three reports, full column census
(`_caiso225_watch_results.json` `W2_constraint_family`):

* `PRC_CNSTR` (DAM): …`TI_ID`, `TI_DIRECTION`, `CONSTRAINT_CAUSE`, `MW`
  (the shadow-price value column), `GROUP`. **No limit, no flow.**
* `PRC_NOMOGRAM`: …`NOMOGRAM_ID`, `CONSTRAINT_CAUSE`, `PRC`, `GROUP`.
  **No limit, no flow.**
* `PRC_RTM_FLOWGATE`: …`TI_ID`, `TI_DIRECTION`, `CONSTRAINT_CAUSE`, `PRC`,
  `GROUP`. **No limit, no flow.**

The corridor identities remain live in the family — the 2026-08-25 nomogram
day-list carries `30750_MOSSLD_230_30797_LASAGUIL_230_BR_1_1`,
`30765_LOSBANOS_230_30790_PANOCHE_230_BR_2_1`, Midway–Vincent #2,
Midway–Whirlwind, and causes `PG1 GATES-LOSBNS_1 500` / `PG1 MOSSLD-LOSBNS
500` — shadow prices only, exactly the caiso-218 route-4 posture ("outcomes
only"). The OASIS Interface Specification remains the **Fall-2017 v5.1.x
family** (v5.1.1 clean 2017-06-22 / v5.1.2 clean 2017-10-27; nothing newer
publicly indexed; developer.caiso.com's library is login-walled but the live
API is the operative test and concurs). No spec revision, no new column.

## §3 — W-3: DMM element limit MW beyond the 2023-annual scalars. **NULL** — two NEW documents tested

Since caiso-218's fetch set (2023 annual / 2024 annual / Q3-2025), DMM has
published exactly two new reports; both were fetched in full and grepped
(text-extracted; every scalar-shaped candidate examined in context):

| new document | published | element limit MW? | what it DOES print |
|---|---|---|---|
| Q4-2025 quarterly | 2026-03-31 | **NO** | element identities + binding shares ("Gates-Midway #1 … bound in 11 percent of hours over the quarter"; Panoche–Gates #2 in 16 %) + per-LAP price impacts + binding windows (HE8–16 solar hours) |
| **2025 Annual** | **2026-06-26** | **NO** | DA top-3 for 2025: Moss Landing–Las Aguilas #1 (**bound ~24 % of hours**; PG&E +$0.8/MWh), Panoche–Gates #2, Gates–Midway #1; 15-min/WEIM top-3: Gates–Midway #1, Tesla–Los Banos #1, Los Banos–Gates #1 (Table 5.1 top-50, price impacts only); windows HE9–15/HE10–16/HE11–16 |

No 2026 quarterly exists yet (reports page checked 2026-08-30). The **2023
annual remains the only element-limit-MW vintage** — the caiso-224 F2
single-vintage insufficiency stands unrepaired by publication.

Two enrichments recorded, no verdict moved: (a) the 2025 annual's Moss
Landing–Las Aguilas ~24 %-of-hours keeps the caiso-224 **F1 0.27 ceiling
class current for 2025** (it was built from the 2023/2024 record's 24–27 %);
(b) the corridor census itself is re-confirmed for 2025 with fresh binding
shares and windows — the census's element identities remain the right ones.

## §4 — The caiso-224 F2 WATCH: corridor outage/derate windows. **NULL** — with one dated pointer

* **OASIS `TRNS_OUTAGE`** (2026-08-10..26 pull, 4,490 rows): the outage
  universe is 28 TI_IDs, all boundary objects (ITCs, `MALIN500_ISL`,
  `PATH_WOR`, Mead-area BGs). None of Tesla–Los Banos #1 / Moss Landing–Las
  Aguilas / Gates–Midway #1 / Panoche–Gates appears as a TI. The
  `OUTAGE_NOTES` field names internal equipment **only where it curtails a
  boundary OTC** (e.g. "OMS 19624758: TABLE MOUNTAIN-TESLA (TABLE MOUNTAIN
  SCAP)" on `MALIN500_ISL` — that is Table Mountain–Tesla on the COI, not our
  Tesla–Los Banos) — 68 distinct note strings, zero corridor elements.
* **CAISO's own transmission outage reports** (the 7-day hourly and
  1000-day daily reports at `content.caiso.com/transout/`) are
  **certificate-restricted** — the market-participant wall, i.e. the
  caiso-222 route-(ii) access class the owner **DECLINED** — and
  forward-looking only, with no public historical archive.
* **FERC Order 881 status** (the one genuinely new fact, and it is a DATE,
  not a fire): CAISO's AAR implementation is delayed — OATI webLineR
  submission go-live targeted April 2026, tariff effective date **no later
  than 2026-12-01**. The ratings database is participant-facing by design
  (ICCP/EMS + the Order's password-protected-website transparency class; BRS
  Track 1) — not a public posting. CAISO's own named future work is to fold
  hourly AARs into **nomograms, TTC/ATC and scheduling limits** — which is
  precisely the machinery behind the W-1/W-2 objects. **The Order-881
  effective date is therefore the next natural re-check trigger for this
  sweep** (see §7).

The transmission-outage derate channel remains **unpublished for these
elements**; the WATCH stands exactly as caiso-224 §D recorded it — not armed,
rule-13 admissible *if it ever exists*.

## §5 — The caiso-131 A3 ask: the SoCalGas OFO declaration record. **AVAILABLE + FEASIBLE; UNFUNDED**

The availability/feasibility report the charter scoped (no intake performed):

* **The record EXISTS, is PUBLIC, and is exactly the required grain.** The
  SoCalGas Envoy public site serves two event-history pages, no login:
  * **Low OFO/EFO Event History** (`/Public/ViewExternalLowOFO.getLowOFOEvent`)
    — 2015–2026 on-page, one column per year; per event: gas-day date,
    stage (1/2/3/3.1/3.2/3.3, EFO), tolerance % (negative = low-side), waived
    flags. Counts: 2015: 3, 2016: 76, 2017: 84, 2018: 136, 2019: 109 (the
    Aliso era), 2020: 59, 2021: 60, 2022: 38, **2023: 43, 2024: 34,
    2025: 25**, 2026 YTD: 11.
  * **High OFO Event History** (`/Public/ViewExternalOFO.getOFOEvent`) —
    **1997–2026**; 2023: 196, 2024: 102, 2025: 189 events.
* **The Jan-2023 blowout cluster is present in the low-side record** — Jan 3
  (Stage 3.1), Jan 4 (3.3), Jan 5 (3.1), Jan 12 (3.1), Jan 13 (3.2), Jan 19
  (3.3) — the exact window caiso-131 §6 identified as the 2023 tail driver.
  The full 2023–2025 low-side event lists are embedded in
  `_caiso225_watch_results.json`.
* **Cycle-level detail and export exist**: the per-day calculation pages
  (`ViewExternalOFO.getOFO` / `ViewExternalLowOFO.getLowOFO`) accept a
  historical `gasFlowDate` (verified live for 2024-01-15: full per-cycle OFO
  declared/stage/tolerance plus forecasted receipts, sendout and storage
  balancing limits) and carry CSV/PDF export actions. OFO declarations also
  post as Critical Notices under Tariff Rule 30 (searchable public ledger).
* **Feasibility: trivial.** Two public GETs + an HTML table parse; fits the
  standard data-intake pattern (schema → fetch script → `write_clean` seam)
  with no wall, no auth, and no observed retention cliff (the high-side
  history reaches 1997). A funded intake session's remaining work is the
  rule-13/24 adjudication of *how* the event record enters (caiso-131 §6's
  own framing: the trigger must come from the OFO event record or not at
  all) and its schema/precommit — not source archaeology, which is now done.
* **Context, stated honestly**: A3 was filed as the one intake that could
  make C3c-2024 *reachable*. C3c is today the keeper's single ledgered caveat
  under the standing rule, so the intake's yield is a future C3c root-cause
  arm (making the tail *real* rather than excused), not a gate need — and it
  is **C3c-side, orthogonal to C3a**. Funding remains an owner decision;
  nothing here performs or recommends it.

## §6 — Adjudication: NOTHING FIRES

Per the caiso-222 §(i) pre-stated trigger duty, a firing watch would have
re-opened as a data-intake charter. None fired:

| watch | verdict | basis |
|---|---|---|
| W-1 (BG re-enforcement) | **NULL** | ERR 1000 both BGs; universe zero-internal (§1) |
| W-2 (limit/flow column) | **NULL** | live columns + spec unchanged (§2) |
| W-3 (DMM element MW) | **NULL** | both new documents print shares/impacts, no MW (§3) |
| caiso-224 F2 (derate windows) | **NULL** | TRNS_OUTAGE boundary-only; participant walls intact (§4) |
| caiso-131 A3 (OFO record) | **AVAILABLE, unfunded** | not a watch-fire; an owner funding option, C3c-side (§5) |

No data-intake charter opens. The caiso-218 §F.2/§F.3 fences were not
approached: nothing was backed out of binding hours or split counts, and no
static single-link object was revived. The DMM caps were not touched (the
caiso-224 DO-NOT-REDO).

## §7 — The frontier, re-affirmed; the Q1 question back to the owner

The frontier after this sweep is **exactly the caiso-222 §9 state**:

* Keeper `2026-08-26-caiso-220-c1-crosswalk`, NOT-YET on C3a alone
  (+4.0 PASS/+12.5/+15.5 %), C3c the single ledgered caveat — the **terminal
  rest with a decision map** (Q1 = option 3, owner-ruled 2026-08-30).
* Route (i), the publication watches: **armed and all NULL today** (this
  sweep). Route (ii), CEII access: **DECLINED** (owner). Route (iii), the
  sub-zonal program: representation standing, its static-cap arm **R**
  (caiso-224), re-armable only through the same (i)-class data that is null
  today.

**Therefore, per the charter: with every data route null, the caiso-222 Q1
C3a disposition question is put back to the owner as the sole remaining route
at this grain.** The question and its full price are already on the record —
`ASSESSMENT-caiso222…` §1(a)–(c): status-quo NOT-YET / the 3–4-motion rubric
amendment (three ISOs flip to full CALIBRATED, the NYISO cascade consumes the
C3c lone-guard) / the accepted terminal rest the owner chose. This packet
re-derives none of it (DO-NOT-REDO §8.1) and recommends nothing (§8.3); it
reports only that **no watch has produced the data that would open any other
route**. If the owner rules nothing, the terminal rest simply stands — that
is what option 3 means, and this sweep is its first scheduled heartbeat.

**The next sweep has a date**: re-run after the Order-881 effective date
lands (≤ 2026-12-01, §4) — the first event with a stated mechanism for
changing the W-1/W-2 answers — or at the next DMM publication (the 2026
quarterlies), whichever comes first. Until one of those dates, re-running
this sweep would be the re-survey the fences forbid.

## §8 — Records and filed items (CAISO lane only)

* This ASSESSMENT; `results/calibration/_caiso225_watch_results.json` (all
  five tests' measured outputs, including the full 2023–2025 low-OFO event
  lists and both TI universe censuses).
* `docs/calibration-log/caiso.md`: caiso-225 entry.
* **Matrix: NOT touched** — no mechanism was tested, no cell verdict moves,
  no queue status changes (the watches were armed by caiso-222 §9 and remain
  armed; the fsno cell's R and its re-arm feeds are unchanged). Charter
  compliance: "matrix §5 queue touch only if a status changes" — none did.
* Keeper, keeper shards, `calibration-complete.json`, `holdout-freeze.json`,
  every other ISO's files: **UNTOUCHED**.
* Filed items: **4 carried** (standing duty); **9 carried** (the CEII wall —
  its Q2 decision map now carries this sweep's null as its first execution).
  New filed item: **10 — the A3 OFO intake is AVAILABLE+FEASIBLE and priced
  at "trivial"** (§5); it waits on owner funding and is C3c-side.

## §9 — DO-NOT-REDO (adds; the caiso-202 §I … 221 §G / 222 §8 / 224 §G chain carries whole)

1. **Never re-run this watch sweep before a dated trigger** — the next
   sanctioned re-check is after the Order-881 effective date (≤ 2026-12-01)
   or the next DMM publication, whichever is first (§7). The tests
   themselves, their endpoints and their null baselines are all in
   `_caiso225_watch_results.json`; a re-run reproduces them in minutes.
2. **Never re-survey Envoy for the OFO record's existence** — §5 IS the
   availability answer (endpoints, spans, counts, grain, export routes,
   verified historical query). The only open A3 work is the funded intake
   itself (schema + rule-13/24 adjudication + precommit).
3. **The 56 → 58 TI-universe delta is adjudicated** (SunZia + Pinal Central,
   external new-build) — do not re-open it as a possible internal-path
   appearance.
4. Carried live from caiso-222 §8.2: these watch tests remain the ONLY
   sanctioned re-checks of the caiso-218/219 walls.

## Closing state

Keeper **`2026-08-26-caiso-220-c1-crosswalk`** UNCHANGED — NOT-YET on C3a
alone (+4.0 PASS / +12.5 / +15.5), C3c the single ledgered caveat. Every
armed watch NULL; the F2 derate watch standing; A3 AVAILABLE+FEASIBLE and
unfunded; no data-intake charter opened; no cell verdict moved; nothing
armed; nothing registered; ZERO SOLVES. The terminal rest (caiso-222 §9 Q1 =
option 3) **stands re-affirmed**, and the Q1 disposition question is back
with the owner as the sole remaining route at this grain. Next sweep date:
post-Order-881-effective (≤ 2026-12-01) or the next DMM publication.
`calibration-complete.json` (no CAISO marker) and `holdout-freeze.json`
(ACTIVE) untouched; no out-of-training year touched or read. **THE OWNER
MERGES.**

**Next number: caiso-226.**
