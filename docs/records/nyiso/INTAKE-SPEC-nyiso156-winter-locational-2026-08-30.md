# INTAKE SPEC — the NYISO winter locational identification intake (Q1 ruling A, executed)

**Filed:** 2026-08-30, session nyiso-156 (ruling-execution continuation).
**Authorization being executed:** the owner's Q1 ruling on
`docs/DECISION-CARD-nyiso156-2025-offer-level-2026-08-25.md`, delivered
2026-08-30 via the in-session decision card: **OPTION A — "Authorize winter
intake"**, on the option text *"Authorize/fund the BLOCKER-B identification
intake: MyNYISO-grade access to the as-enforced sub-zonal in-city commitment /
AORR parameters (and/or a source splitting the Capital_Hudson seam leg)"*.
**Nothing is armed or solved by this document.** It converts the ruling into
two executable legs with their gates, owners, and stop conditions stated
before any work runs.

**The object this intake serves:** the winter face of the C3a-2025 failure —
Jan+Feb 2025 downstate under-pricing worth **−$3.92/MWh of the annual
load-weighted mean** (whole-month, sustained; upstate near-exact; model
gradient $0.81 vs actual $14.83), per
`results/calibration/_nyiso156_offer_level_phase0.json` M1/M4/M6. Closing this
face alone returns C3a-2025 to ≈ −5.3 % (in band) and the determination to
CALIBRATED via the C3c standing rule (card §4).

---

## §0 — A RECORD CORRECTION THE RULING SURFACED

The nyiso-150 assessment (§4 item 2) and, inheriting it, the nyiso-156 card
(§3 item 1) both describe the seam half as *"UNIDENTIFIABLE from public data
(the `SCH - PJ - NY` leg spans the cutset and neither P-32 nor PJM's tie file
splits it — nyiso-125's rule-20 refusal, standing)"*. **That phrasing was
STALE when written.** The nyiso-125 refusal was **discharged on
identification the same day it was filed**: nyiso-126
(`FINDING-nyiso126-seam-identification-and-c3a-decomposition-2026-08-04.md`
§1, log entry 2026-08-04: *"do not re-derive the nyiso-125 refusal — it is
discharged on identification"*) identified the split from **NYISO's own
published posting** with **zero free parameters**, filed
`PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md`, and left the lane
**owner-gated, not data-blocked**. The correction changes no measurement and
no verdict; it changes which leg of this intake a session can execute without
the owner fetching anything. (Card and matrix carry matching annotations,
same commit as this spec.)

## §1 — LEG 1: the eastern-seam PAR attribution (SESSION-EXECUTABLE; the owner gate is now LIFTED)

**What it is.** Replace the model's unattributed split of the measured
`SCH - PJ - NY` PJM AC interchange with NYISO's published attribution across
the zones its ties land in: Ramapo 32 % + JK 15 % → `Capital_Hudson` (Zone G),
ABC 21 % → `NYC` (Zone J — a new AC border path the model does not carry
today), residual 32 % → `Upstate_West` (Zone A), availability-conditioned by
the posting's own PAR-outage reallocation rule. Source: NYISO, *"NY-NJ PAR
Interchange Percentages, Operational Base Flow (OBF), and other MW Offsets"*
(nyiso.com/documents/20142/2268509/NY-NJ_PAR_Interchange_and_OBF.pdf;
percentages effective 5/1/2017, OBF 0 MW since 11/1/2019). All eight
percentages are published constants; PAR in-service state is measured.

**The intake this leg needs** (the prereg's §4, the reason it was
owner-gated): **NYISO MIS P-34 `ParFlows`, 2023–2025** — 5-minute measured
flow per PAR PTID, ~87 MB zipped, **public MIS (no login), verified fetchable
at nyiso-126**. Intaken under the repo data contract (data-intake discipline:
`data/raw/` immutable download + schema + curation to `data/clean/`), cited
as the availability input for the outage-reallocation rule. The eight
percentages need no intake (cited constants).

**Execution conditions, binding on the executor session:**

1. The A/B runs under the STANDING pre-registration
   (`PREREG-nyiso126-eastern-seam-attribution-2026-08-04.md`) — its DOF
   ledger (§3: four published shares + measured availability, `n_residual`
   stays 6), kill gates K1–K7, decision rule and named adverse cases are
   already on the record and are NOT re-negotiated. Its ex-ante prediction
   P3 stands: **the seam attribution is NOT predicted to close C3a-2025**
   (the miss is decile-10 concentrated); if it does, that is investigated,
   not banked.
2. **Baseline refresh, reported not re-specified:** the prereg's K6 pins the
   control to the nyiso-125-era keeper's C3a (±0.2 pp). Twenty-six days and
   six keepers later, the honest reading is a same-HEAD zero-delta replay of
   the CURRENT keeper (`2026-08-25-nyiso-155-hydro-repair`) as control —
   per the nyiso-115/117/119 lesson, the executor re-specifies K6 onto what
   it meant (control reproduces the CURRENT keeper's committed scorecard)
   and reports the original wording alongside. The G1 drift class
   (nyiso-155: 2023/2024 reshuffle at new HEAD) applies — never score the
   arm against the committed keeper's bytes.
3. **The companion chain is the point.** nyiso-150 §2.2 proved the LP prices
   the four mainland zones as one coupled block (an $8–13/MMBtu measured
   zonal gas spread yields < $1 of price spread) and adjudicated
   `nyiso_iroquois_winter_spread` `O → R` with the re-open condition
   *"re-test as the companion of a locational mechanism that lets the
   west→east cutset bind — never alone"*. **If and only if** the seam arm
   passes its own gates AND measurably lets the west→east cutset bind in the
   winter event months, the iroquois fuel-side flag becomes re-testable as
   its pre-registered companion (a second arm in the same session, its own
   prereg section, R-cell re-open on the recorded condition — new evidence
   exists, so the DO-NOT-REDO discipline is satisfied).
4. Rule 28 duty (c): the four share constants enter `ScenarioConfig` with a
   matrix base row + all-six-shard cell lines in the same PR. Rule 15: both
   arms registered whatever the outcome. Rule 16: 2023 2024 2025, one
   invocation each arm. Freeze ACTIVE: no other year.

## §2 — LEG 2: the MyNYISO as-enforced AORR access (OWNER-EXECUTABLE ONLY)

**What it is.** The in-city (Con Edison, NYC Zone J) sub-zonal commitment
formation — BLOCKER-B proper. nyiso-97
(`docs/FINDING-nyiso97-load-pocket-identification-2026-07-29.md`) established:
the as-enforced requirements live in the **Applications of the Reliability
Rules (AORR)** table, reachable only through the NYISO **Reports & Info**
page behind a **MyNYISO login** (nyiso.com/reports-information →
nyiso.com/login); the current Manual 12 replaced its former Appendix B tables
(B.1–B.5) with links to that walled location; nysrc.org posts no copy. The
public 2008-vintage Appendix B was adjudicated **non-identifying on content**
(every Con Ed in-city commitment row qualitative and condition-triggered,
parameters in unpublished Con Ed SO procedures such as SO3-18).

**What the owner fetches** (a session cannot — no credential access, and
nyiso-97's authorization variant was stop-if-walled):

| artifact | where | what it must contain to identify |
|---|---|---|
| The **current-vintage AORR table** (all Con Edison and LIPA rows, esp. the successors of Table B.4 LRR 1–3, ARR 37, ARR 66, ARR 28) | MyNYISO → Reports & Info | per-pocket **MW levels or minimum-units-online**, **eligible unit sets**, and **observable triggers** — the three quantities nyiso-97 §1 requires |
| Any Manual-12-linked replacement tables for the former Appendix B | same portal section | same test |
| The effective-date/versioning page for the above | same | vintage coverage of 2023–2025 (a single current snapshot that postdates the span must state what changed) |

**The identifiability gate, pre-committed (nyiso-97 §4 re-run):** on receipt,
a session re-runs the nyiso-97 content test against the CURRENT vintage. PASS
= at least one 2023–2025-applicable NYC pocket row carries a derivable MW /
min-units / eligible-set parameter with an observable trigger and a rule-13
forward story — then, and only then, a mechanism prereg is written (P1-native
commitment-bridge class, per the three existing bridges). FAIL = the rows are
as qualitative as the 2008 vintage — **the leg closes with cause exactly as
nyiso-97 closed**, the winter face stays open on the Leg-1 chain alone, and
nothing is inferred from conduct, BPCG uplift, LBMP, or the residual
(nyiso-97 §5's re-open bar, restated verbatim as binding here).

**What access does NOT license:** no parameter may be backed out of the
residual to "fill in" a qualitative row; make-whole/BPCG data is an outcome,
not a requirement (rule 13); the ledgered C3c queue stays closed regardless
of what the table shows.

## §3 — WHAT THIS INTAKE DOES NOT AUTHORIZE

* No holdout spend (freeze ACTIVE; every solve year ∈ {2023, 2024, 2025}).
* No re-tune of the hydro input pair (rule 14; volume tautological under the
  930 pin).
* No C3c lever, no scarcity parameter anywhere in either leg (rule 19 — the
  nyiso-126 construction explicitly carries none).
* No re-opening of the refuted routes: Tier-3 TTC re-grounding (BLOCKER-C),
  the F/G topology split (charter closed at G0, nyiso-124), the bare Zone-K
  number swap, the fuel-side iroquois flag ALONE.
* No determination change without D-5(b): any promotion out of Leg 1 follows
  the standing prereg's decision rule, and a worse re-verified determination
  stops and escalates.

## §4 — SEQUENCING AND EXPECTED EFFECT, STATED HONESTLY

Leg 1 is executable immediately by the next lane session (intake + A/B, one
session); Leg 2 waits on the owner's fetch and can proceed in parallel. The
measured expectation chain, pre-registered here so the outcome can be judged
against it:

1. The seam attribution alone moves the downstate LEVEL/gradient (prereg P2)
   but is NOT predicted to close C3a-2025 (prereg P3).
2. The winter face closes only if the locational chain (seam attribution →
   west→east cutset able to bind → iroquois companion re-test) reproduces the
   downstate winter premium from measured fuel + published attribution — or
   if Leg 2 identifies the in-city commitment formation.
3. Either face closing (winter −3.92 or summer −3.94) returns C3a-2025 to
   ≈ −5.3 %, in band (card §4). The summer face needs neither leg — it is
   the ledgered C3c limitation and stays ledgered.

A chain that stalls at any gate is reported at the gate, with the stop named
— a stall is a legitimate outcome of an identification intake, not a failure
of the session that reports it.
