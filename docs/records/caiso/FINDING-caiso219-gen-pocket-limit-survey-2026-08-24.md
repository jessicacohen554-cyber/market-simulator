# FINDING — caiso-219: THE §F.3a GEN-POCKET EXPORT-LIMIT PHASE-0 SURVEY — a SECOND decisive null on the prerequisite (CAISO publishes sub-zonal deliverability as an *accreditation headroom* in a resource-weighted currency, never a flow rating), and a RE-LOCATION of the hypothesis: CAISO's own off-peak constraint record puts the belly-hour sub-zonal mass in PG&E Kern/Fresno at the GATES–MIDWAY complex (ZP26 side), with Tehachapi (SP15) carrying ZERO off-peak constraints (2026-08-24)

**Authority:** owner 2026-08-24, answering the caiso-218 §E decision item —
"open the §F.3a strandedness lane instead" (declining the caiso-217 replay).
This is that lane's Phase 0. NO LP, NO SOLVE, nothing armed, nothing
registered, no cell verdict moves. The caiso-201 rest is undisturbed for
chartered work; the queue stays EMPTY.

**The one-line verdict:** the §F.3a prerequisite — a citable Kern/Tehachapi
collector **export limit in flow MW** — **does not exist**, and the reason is
now precise rather than "half-found": CAISO *does* publish a rich, annual,
machine-readable sub-zonal constraint record (93 named deliverability
constraints with MW), but every MW in it is **accreditation headroom for
additional queued generation, denominated in on/off-peak resource output
factors** — not a transmission rating (§C). The published *rating* is the
CEII object caiso-218 route 7 already walled. **But the survey is not empty:**
the same record carries an explicit ON-PEAK/OFF-PEAK binding flag, and it
says the belly-hour sub-zonal constraint mass sits in **PG&E Kern (7/10) and
Fresno (14/19)** — the **Gates–Midway** complex on the **ZP26** side — while
**Tehachapi (SCE Northern) is 0/3 off-peak**. §F.3a's pocket, as written
("Kern/Tehachapi collector … inside the southern zones"), is **mis-located**
(§D). Per the charter, no intake is proposed and no solve is asked; **NOT-YET
stands** (owner ruling 5).

---

## §A — Standing state at MY HEAD (verified, not inherited)

Verified against committed artifacts at `3ca40e9`:

* Keeper **`2026-08-17-caiso-200-h1-memberpanel`** (`frontend/data/backcast/keepers/CAISO.json`).
  NOT-YET, rubric v3.4; **C3a the sole load-bearing FAIL at +4.1 / +12.8 /
  +15.7** (2023/2024/2025 vs the ±10 band); C3c the single ledgered caveat;
  C1 12/12, free 8/8; DOF 10/7. No `complete`/`final` marker; freeze ACTIVE;
  **2023–2025 only**.
* **Committed C3b baseline 0.098 / 0.179 / 0.182** (caiso-209 correction,
  caiso-213 re-verification). Any future gate table cites THIS, never the
  caiso-218 handoff's uncommitted 0.100/0.177/0.180.
* The **caiso-217 registration debt is OPEN and now owner-declined** — the
  owner chose this lane over the replay, so filed item EIGHT stands unchanged:
  the crosswalk remains committed data whose solve-side effect is unscored,
  and the 2023 checkpoint sidecars remain a stranded artifact. Nothing in this
  session changes that.

## §B — The survey table (Phase-0 deliverable 1)

Routes walked with live fetch tests (2026-08-24 UTC). caiso-218 §B routes are
**not** re-walked (DO-NOT-REDO item 1); this table covers the *deliverability*
class that caiso-218 §D left open. **Walls in bold.**

| # | route | object & grain | span / vintage (tested) | alignment to a model `Flow` bound | fetchability | verdict |
|---|---|---|---|---|---|---|
| 1 | **Attachment A — Transmission Capability Estimates** (annual IRP input worksheet) | per named **deliverability constraint** × affected resource location × **On-Peak/Off-Peak flag**: FCDS + EODS capability MW, ADNU/AOPNU increments & costs | annual series **2019 / 2021 / 2023 / 2024** (each "replaces" the prior); 2024 = current | **MISALIGNED on four independent axes** (§C): currency, scope, nesting, vintage | proven — 33.7 KB XLSX, 93 constraints parsed | **WALLED as a limit; ADMITTED as the structural census (§D)** |
| 2 | **TPD Allocation Reports** (annual) | per Area Constraint: overloaded facility + contingency + **Overload %**, project membership (queue/POI, DFAX circle), TPD allocation MW | 2024 (120 pp) + 2025 (119 pp) fetched in full; same constraint sections both years, **year-varying** (Windhub Total TPD 2,400.0/1,754.1 → 2,448.0/1,816.7) | the constraint tables publish **"Overload %" of an UNPUBLISHED rating** — checked across every constraint table in the 2025 report: 100 %, 102 %, 104 %, 105 %, 109 %, 110 %, 114 %, 117 %, 122 % — **never a MW limit** | proven (PDFs) | **WALLED — percentages, not ratings** |
| 3 | Attachment B2 — Deliverability Constraint Boundary Diagrams | per-constraint electrical boundary (the DFAX circle) | 2024, 9.45 MB PDF | boundary *identity* only; carries no MW | proven | **membership evidence only** |
| 4 | Cluster 15 "Zonal Capacity **Study Limits**" | per CAISO Study Area × technology: FCDS/EODS MW of the **2034 CPUC generic portfolio**, ×1.5 study factor | single 2034 portfolio snapshot | a **portfolio study input for a 2034 forecast case**, not a limit on the as-operated grid | proven (22.5 KB XLSX) | **adjudicated NO — a portfolio, not a limit** |
| 5 | the underlying branch **thermal ratings** (what Overload % is a percentage *of*) | MVA/MW per element | — | this is the only object that WOULD map | CEII / CRR-participant-restricted | **DEAD — same wall as caiso-218 route 7** |
| 6 | LCT reports (re-confirmed, not re-walked) | load-pocket **import** requirements | committed `data/raw/capacity-deliverability/caiso/caiso.csv` (386 rows; `Kern` appears as a *local_area* **requirement**, 439 MW 2023) | import-side; the §F.3a misalignment caiso-216 already named | committed | **WALLED (unchanged)** |

## §C — Why the published MW is not a limit (the rule-14 kill, quantified)

The Attachment A numbers are real, current and machine-readable — and still
inadmissible as a `Flow` bound, on four independent axes. All four are stated
by CAISO itself in the 2024 white paper; the census records them in
`alignment_notes`:

1. **CURRENCY.** Capability MW are denominated in the deliverability study's
   *resource output factors*, not flow MW. White paper Table 3.1-1 (on-peak):
   **solar SCE 13 %, PG&E 15 %**; wind SCE 48 %, PG&E 50 %. Table 3.1-2
   (off-peak): solar 77–79 %, wind 44–69 %, **thermal 0 %**. A midday belly
   flow is ~nameplate; the on-peak number is ~6× off in the very hours the
   C3a residual lives in. (The white paper also records that **off-peak
   deliverability was not performed at all in the 2024 TPD Allocation
   study**.)
2. **SCOPE.** The tables are headroom for *additional queued* generation. The
   existing operational fleet's already-banked deliverability is excluded by
   construction — the 2024 white paper states OTC generation deliverability
   was deliberately **not** added back. A pocket export limit is
   `existing deliverable output + headroom`; the first term is unpublished,
   so the limit is **not recoverable** from the published number.
3. **NESTING.** One location sits behind several overlapping constraints with
   different capabilities — **Tehachapi: Antelope–Vincent 6,149.1 / Vincent–Lugo
   6,733.2 / Windhub 1,333.6 MW** (FCDS). The white paper warns capability is
   "limited by two or more constraints, each of which crosses a [zone]" and
   that nested zones share budgets (its Greater Kramer Z1⊃Z2,Z3,Z4 worked
   example). No row maps onto one model link.
4. **VINTAGE.** The estimates include **ISO-approved-but-unbuilt upgrades** and
   are an IRP planning input for forward portfolios. They describe a future
   system, not the as-operated 2023–2025 grid the backcast solves.

**Fence, restated as a standing kill (§F):** no MW from Attachment A, from a
TPD allocation table, or from the Cluster-15 portfolio may be armed as a
transmission limit. Deriving a rating by dividing a flow by an Overload % is
the outcome pin in a limit costume and is equally forbidden.

## §D — The substantive result: §F.3a's pocket is MIS-LOCATED

Instrument: `scripts/probes/_caiso219_deliverability_census.py` →
`results/calibration/_caiso219_deliverability_census.json` (93 constraints;
no LP, no solve — a parse of the published worksheet). Reading the ON-PEAK /
OFF-PEAK binding flag by interconnection area:

| interconnection area | off-peak / total | side in our topology |
|---|---|---|
| **PG&E Fresno** | **14 / 19** | ZP26 / NP15-south |
| **PG&E Kern** | **7 / 10** | ZP26 |
| SCE Eastern | 4 / 7 | SP15 (east, not a collector pocket) |
| SDG&E | 3 / 12 | SP15 |
| **SCE Northern (incl. ALL Tehachapi)** | **2 / 8** | SP15 |
| East of Pisgah | 2 / 3 | SP15 (east) |
| SCE North of Lugo | 0 / 5 | SP15 |
| SCE Metro | 0 / 2 | SP15 |
| PG&E Greater Bay | 0 / 18 | NP15 |
| PG&E North of Greater Bay | 0 / 9 | NP15 |

Three findings fall out, and they agree with two already-committed facts:

* **Tehachapi is 0/3 off-peak.** Its three constraints (Antelope–Vincent,
  Vincent–Lugo, Windhub) are **On-Peak only**. The collector §F.3a names as
  the southern gen-pocket is, per CAISO's own record, **not** an
  oversupply-hour constraint. The two SCE-Northern off-peak constraints are
  South of Magunden and Antelope–Neenach — neither is the Tehachapi collector.
* **The off-peak mass is at GATES–MIDWAY.** The 21 PG&E Kern+Fresno off-peak
  constraints are dominated by that complex: Gates 500/230 kV TB #11 and #12,
  Diablo–Gates 500 kV, Gates–Arco 230 kV, Cal Flat–Gates 230 kV, Midway
  230/115 kV TB #3, Semitropic–Midway 115 kV, Kern–Tevis–Stockdale–Lamont.
  That is the **southern terminus of Path 15** — and it **independently
  corroborates caiso-218 §C**, which concluded from the DMM record that
  reality binds the corridor's *elements*, not the cut. Two unrelated
  published records now say the same thing.
* **It corroborates the committed caiso-217 zonal fact** that ZP26 reads
  *below* SP15 in reality (MCC −4.7 vs −2.8) — "a finer structure than the
  pool carries". The belly-hour internal constraint record puts that finer
  structure on the **ZP26 side**, exactly where the price record put it.

**Consequence for §F.3a.** The hypothesis's *mechanism* (sub-zonal
strandedness behind an internal constraint, in belly hours) survives and is
in fact strengthened. Its *location* does not: it is written as a southern
(SP15) Kern/Tehachapi collector pocket, and the evidence places the
off-peak-binding structure on the **ZP26/Fresno–Kern Gates–Midway** side.
A future §F.3a proposal must re-derive its pocket from this census, not from
the caiso-216 wording. **This is a survey result, not a proposal — nothing is
proposed today**, and the §C fence means no such pocket is proposable until
a rating source exists, which today it does not.

## §E — The ask (deliverable 4): NOTHING

Phase 0's answer is again a decisive null on the prerequisite, so per the
charter **this lane asks for no intake and no solve**. NOT-YET stands on the
committed caiso-200 keeper.

Both named C3a successor levers (§F.3b internal-path limits, caiso-218;
§F.3a gen-pocket export limit, this session) are now **blocked on the same
single object: a published transmission RATING for internal CAISO elements**,
which is CEII. That is the honest state of the C3a lane, and it is a
structural wall, not a work backlog. What remains open is §F.3c (the measured
export sink) — still contingent on a **C3b trip that has not fired** — and
whatever the owner may authorize as a non-limit representation. No default is
assumed and nothing is recommended by this FINDING.

## §F — Records, fences added, filed items (rule 28b — CAISO shard only)

Committed by this session (branch `claude/caiso-path-limit-survey-dvrpn0`):

* This FINDING; `scripts/probes/_caiso219_deliverability_census.py`;
  `results/calibration/_caiso219_deliverability_census.json` (93-constraint
  census + output factors + alignment notes).
* `docs/calibration-log/caiso.md` caiso-219 entry; matrix §5.2 caiso-219
  block; CAISO shard evidence append (**NO verdict moves — nothing was
  tested**).

DO-NOT-REDO additions (append to the caiso-202 §I / 215 §I / 216 §I / 218 §F
chain):

1. **Never re-survey CAISO's deliverability record for a gen-pocket export
   LIMIT.** The record is complete and censused here: capability MW is
   accreditation headroom (§C axes 1–4), TPD tables publish Overload % of an
   unpublished rating, and the rating itself is CEII. Re-opening requires a
   CAISO publication change, not another search.
2. **Never arm a MW from Attachment A, a TPD allocation table, or the
   Cluster-15 portfolio as a transmission limit**, and never back a rating out
   of a flow ÷ Overload %.
3. **Never propose the §F.3a pocket at Tehachapi/SP15 on the caiso-216
   wording alone** — the census says Tehachapi is 0/3 off-peak and the
   off-peak mass is ZP26-side at Gates–Midway (§D). Any future gen-pocket
   proposal derives its location from `_caiso219_deliverability_census.json`.

Filed items: **NINE** — carrying caiso-218's eight (incl. the now
owner-declined caiso-217 registration debt) and adding **NINE: both ranked
C3a successor levers are blocked on the same CEII rating object** (§E), which
is the item the owner would need to route around for the C3a lane to move.
Cross-lane items THREE carried unchanged, plus the caiso-213-routed matrix
anchor item.

Keeper, markers, freeze, DOF ledger, every cell verdict: **UNCHANGED**.

**Next number: caiso-220.**
