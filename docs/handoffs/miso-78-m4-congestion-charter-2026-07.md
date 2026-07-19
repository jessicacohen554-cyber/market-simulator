# miso-78 — M4 congestion charter: representation adjudication for the fetchable per-flowgate limit series

**Status: DRAFT — PENDING OWNER SIGN-OFF. Verdict: NO-BUILD (data-blocked-at-representation).**
**Date:** 2026-07-19. **Lane:** the M4 congestion charter mandated by the frozen
miso-76 charter (`docs/handoffs/miso-nc-price-separation-design-2026-07.md` §3
M4 — "gets its OWN charter") after the miso-77 feasibility investigation
returned GO (qualified) (`docs/handoffs/miso-77-m4-afc-feasibility-2026-07.md`).
**Discipline:** charter-first — this document is committed BEFORE any intake,
derive, or LP code; the adjudications in §2 and the reopening conditions in §6
are pre-registered and may not be revised after sign-off except by a successor
charter (§7). Per CLAUDE.md rule 27 this lane is Fable/Opus-assigned. NO LP was
solved, NO data was intaken, and NO code was written for this document.

**The one-line verdict:** miso-77 proved the *limits* are fetchable; this
charter finds the *network* cannot consume them honestly. A branch-level MW
limit prices a zonal boundary only through shift factors, nothing publishes
shift factors (findings §2c), and every apportionment-free representation
candidate is inert while every non-inert candidate invents the apportionment
the M1 refutation already refused. The honest outcome — anticipated as a valid
end state by the miso-77 handoff and by rule 1 — is a NO-BUILD charter that
records the congestion component beyond existing structure as
**data-blocked-at-representation**, with pre-registered reopening conditions.

---

## 0. Scope

**This charter owns:** the decision of whether and how the fetchable M2M/CMP
per-flowgate limit series (miso-77 findings §2a/2b — hourly FFE, daily
allocation-implied total ratings, OASIS seasonal ratings + TRM/CBM statics,
flowgate registry) can enter the 6-zone MISO LP as a congestion mechanism, and
the resolution of the five items the findings §5 put to it (crosswalk, no-PTDF
representation, cap-series choice, East disclosure, intake mechanics).

**Out of scope (untouched, own lanes/ledger):** the irreducible C3a-2025/C3c
scarcity tail; the declined miso-76 determination path (un-applied, no fresh
owner ask); direction-symmetric losses; the D1 Michigan(Z7)/Wisconsin(Z2)
split; the all-ISO `gas_daily_shape` interp fix; the PJM merit-cap twin. The
existing congestion structure — CIL/CEL seasonal envelopes, the RDT L7 pair +
TCDC pricing, the measured seam ladders (`MISO_SEAM_LADDER_BY_YEAR`,
`MISO_SEAM_DIBA`) — is not modified by this charter in any way.

## 1. The representation problem (the question this charter stands or falls on)

Three measured facts, none of which this charter may wish away:

1. **The fetchable limits are branch-level.** Every series in the fetchable
   universe keys on a NERC flowgate — a monitored transmission element plus
   contingency — not on any element of the model's 6-zone reduced network
   (links L1–L7, seam interfaces, CIL/CEL boundaries).
2. **The congestion mass is mostly intra-zone.** The miso-76 probe-3 ranking
   (DA bc_HIST Σ|shadow price| by model-zone boundary, location-only
   answer-class use): West-internal 20–26 %, external/seam 20–32 %,
   Plains-internal 10–15 %, Indiana-internal 7–11 % — and **clean
   between-model-zone corridor pairs barely register (peak 0.8 %)**. The
   miso-77 coverage table reproduces the same anatomy inside the fetchable
   universe. There is nothing for a corridor cap to cap.
3. **Nothing publishes shift factors.** No PTDF/shift-factor data exists
   anywhere in the M2M/CMP/OASIS family (findings §2c), and the hourly
   operationally derated limit is likewise unpublished. The zonal price
   expression of a binding branch constraint *is* its shift-factor pattern —
   without one, a branch MW limit has no admissible projection onto zonal
   injections or inter-zonal flows.

So the admissibility of the *input* (the rating series passes rule 13's
forward-regeneration test, §4.2) does not confer representability: between the
measured limit and the 6-zone LP sits a coefficient set the data does not
supply. The M1 refutation (miso-76 charter §3: a per-link cap "would be an
invented apportionment, exactly what scope decision D4 refused" — the
zonal-refinement §8 decision that chose a documented CIL-sum ceiling over an
estimated intra-union-transfer subtraction precisely because "the subtraction
is itself an estimate") is the standing precedent, and it binds every
candidate below that tries to manufacture that coefficient set.

## 2. Candidate representations, adjudicated (pre-registered, frozen)

Each candidate is stated with its refutation ground. These adjudications bind
any successor charter absent new external facts (§7).

- **RP-1 — Per-corridor MW caps on L1–L6 from crosswalked flowgate ratings:
  REFUTED (M1 redux).** Mapping branch flowgates onto zonal corridors requires
  apportioning each flowgate's limit across parallel model paths — the
  invented apportionment the M1 refutation refused. Independently: fact 1.2
  (between-zone pairs ≤ 0.8 % of congestion mass) makes even a perfectly
  mapped corridor cap inert on the measured anatomy — it would fail the
  miso-76 R3 inertness test by construction while adding tuned-cap surface
  area (rules 13/26).
- **RP-2 — Aggregate boundary-class caps (Σ ratings over a coverage class →
  one model-link cap): REFUTED.** A sum of branch ratings is not a
  simultaneous transfer capability (parallel-path physics; the same reason
  D4 called the CIL sum a *ceiling* and documented it). Assigning the class
  sum to a link assumes unit shift factor on every member flowgate — the same
  invented apportionment at one remove. And the dominant classes
  (West/Plains/Indiana/East-internal) have **no model link to cap at all**.
- **RP-3 — Explicit flowgate rows in the LP over zonal injections/flows, with
  assumed or estimated coefficients: REFUTED.** With no published PTDFs, the
  coefficient set is either (a) assumed — the invented apportionment,
  scope-D4 class; or (b) fitted empirically from the M2M settlement market
  flows or by regressing bc_HIST shadow prices onto zonal spreads — which
  consumes the answer class as an input (rule 13; both series are
  validation-only, findings §4) and would be residual-fitting of exactly the
  kind rules 13/26 name. There is no third source for the coefficients.
- **RP-4 — Generation-pocket deliverability derates behind constrained
  flowgates (ERCOT-GTC analogue): REFUTED.** ERCOT GTCs are *published
  interface definitions* — a named limit over a declared generator set on the
  model's own topology, which is why `ercot_wtx_curtailment_driver` is
  admissible. MISO publishes no mapping from flowgates to generation pockets;
  constructing "which units sit behind FG X" requires electrical
  distance/shift factors → the same invented apportionment. FFE does not
  substitute: it is an entitlement allocated between reciprocal entities, not
  a pocket-deliverability limit.
- **RP-5 — Seam-link limit substitution from the (~90 %-covered) seam-class
  flowgates: REFUTED (misalignment).** M2M flowgates are internal elements
  loaded by seam loop flow, not interchange interfaces; neither Σ rating nor
  Σ FFE over the seam class is a measured limit on the model's seam links.
  This is not a CAISO-MIC analogue — the MIC is a published *interface*
  quantity on the model's own boundary; a flowgate aggregate is defined on a
  different boundary than our representation, the exact misalignment case
  rule 14 carves out. The seam already carries boundary-aligned measured
  structure (RDT L7 + TCDC pricing, `MISO_SEAM_LADDER_BY_YEAR` Q-Q ladders,
  `MISO_SEAM_DIBA` envelopes); replacing it with a misaligned aggregate would
  make the representation *less* faithful.
- **RP-6 — Physics-derived reduced network (public-topology DC model →
  estimated impedances → derived PTDFs → honest zonal reduction): NOT
  REFUTED IN PRINCIPLE — NOT CHARTERED.** This is the only candidate whose
  coefficient set would be residual-independent, physics-grounded, and
  forward-regenerating (rule 13 admissible in principle). It is not chartered
  here because it is a major standalone program, not an intake: MISO's actual
  network model is CEII; public topology sources (EIA/HIFLD) carry geometry
  and voltage class but not impedance, so every branch reactance is an
  engineering estimate; and the fidelity of a ~1,000-flowgate network reduced
  onto 6 zones is unvalidated and unbounded a priori. If the owner ever wants
  the congestion component badly enough to fund this, it is its own lane with
  its own charter (reopening condition RO-2, §6) — pre-committing to it here
  would be scope fiction.

**Exhaustiveness note.** Any representation not listed reduces to one of the
above at the coefficient layer: it either places a branch limit on a network
element (RP-1/2/5), projects it through coefficients (RP-3/6), or converts it
into a resource-side derate (RP-4). The charter therefore treats §2 as
covering the candidate space, and requires a successor charter (not an edit)
for any claimed new class.

## 3. Verdict

**NO-BUILD.** The congestion component of intra-Midwest separation beyond
existing structure (CIL/CEL + RDT/TCDC + seam ladders) is recorded in the
documented-limitation ledger as **data-blocked-at-representation** — an
upgrade in precision from the miso-76 wording "data-blocked" (§3 M4): the
*limit data* now demonstrably exists (miso-77 GO), and the block has moved to
the representation layer, where the missing object is the shift-factor /
network-reduction coefficient set. Recorded, not faked (rule 1): no mechanism
is built, no placeholder is wired, no partial "seam-only" or "top-flowgate"
variant is smuggled in under this charter.

Two corollaries, stated so they cannot be un-stated later:

- **The miso-76 R2 East-2025 cancellation corridor stays open as a ledger
  item** and is *doubly* blocked: ~75 % of East-internal congestion mass is
  outside the fetchable universe (findings §3), and the covered remainder is
  representation-blocked like everything else.
- **No congestion-shaped tuning may cite this charter as license.** A fitted
  hurdle, corridor cap, or zonal adder "informed by" the flowgate data
  remains refuted under RP-1/2/3 and rules 13/26 regardless of how it is
  labelled.

## 4. Resolution of the five findings-§5 items

1. **Crosswalk curation — CONDITIONAL, not executed.** No crosswalk is
   curated under NO-BUILD (see §5 rationale). The frozen conditional spec:
   `data/raw/reference/miso-flowgate-constraint-crosswalk.csv` mapping NERC
   flowgate ID ↔ bc_HIST constraint name ↔ From/To control areas → model
   zones, curated from the registry descriptions + Allocation owner fields +
   normalized station-name token candidates, every row carrying a provenance
   column, human-verified. Frozen against residuals (rule 23): re-derives
   only on registry/source updates, with the data change cited in the
   commit. bc_HIST Σ|SP| ranking may prioritize curation *effort*
   (location-only answer-class use, the miso-77 precedent) but may never
   motivate editing a mapping.
2. **Representation without shift factors — RESOLVED: not achievable
   honestly at 6 zones with published data.** §2 adjudication; the central
   design risk the charter was required to stand or fall on. It falls, and
   says so.
3. **Which series is the cap — ADJUDICATED (for any successor):** the
   **allocation-implied / OASIS total rating** is the admissible input class
   (physical equipment property, two independent publications agreeing
   within ~1 %, seasonal, forward-regenerating — rule 13 pass), with the
   explicit caveat that it is a simultaneous total on a branch, not a
   per-direction market limit on any model element. **FFE is context-only**:
   its forward analogue would require modeling the CMP firm-entitlement
   allocation process, whose inputs (firm reservations, historic firm usage)
   are not published — until a successor charter states a real
   forward-regeneration story, FFE fails rule 12's forward-story test as a
   mechanism input. **The hourly operationally derated limit is unpublished**
   (findings §2c) — any successor build carries that gap as a disclosed
   limitation, and its publication alone does not cure representation
   (RO-4, §6).
4. **East disclosure — STANDS, unconditionally.** Any future congestion
   claim under any reopening scopes to the covered classes (seams ~90 %,
   West ~74–78 %, Illinois ~83–85 %, Indiana ~64–77 %); East-internal
   ~75 % uncovered stays in the documented-limitation ledger and is never
   papered over by a mechanism fitted elsewhere.
5. **Intake mechanics — CONDITIONAL, not executed** (spec frozen in §5).

## 5. Conditional intake spec (frozen mechanics; executed ONLY on a §6 reopening)

**Decision: NO intake under NO-BUILD.** Rationale, pre-registered so it is
not re-litigated: (a) there is no admissible consumer — an intake without one
is dead weight that must still be quarantine-guarded and maintained; (b) a
standing curated crosswalk + limit mirror keyed against the answer-class
location data, sitting next to a refuted mechanism class, is a re-armable
channel of exactly the kind rule 26 exists to prevent (the ORDC-offset
lesson: dormant surface area gets re-swept); (c) the fetch channel and URL
patterns are fully documented in the findings §2/§6 — nothing is lost by not
mirroring now.

If a reopening condition fires, the intake executes as specified here without
re-litigation of mechanics:

- **Datatype** `m2m-flowgate-limits` via the data-intake skill, schema-first
  (`data/dictionary/schema/`): (i) daily Allocation → per-flowgate implied
  total rating MW (admissible input tier); (ii) hourly FFE (context tier,
  promotable only under a stated forward story per §4.3); (iii) registry
  snapshots (crosswalk source). The `M2M_Settlement_srw_YYYY.csv` family is
  **never intaken as clean data** — answer class, validation-only gitignored
  mirror, same standing as bc_HIST.
- **Fetcher** `scripts/data/fetch_miso_m2m_flowgates.py` patterned on
  `fetch_miso_bc_hist.py`: train-window quarantine guard (2023–2025
  hard-fail outside the window absent authorization + marker — MISO has no
  calibration-complete marker), bulk mirrors gitignored with sha256 README
  rows (bc_HIST precedent), `docs.misoenergy.org` plain-curl channel.
- **OASIS statics** (`AFC_FG_RATINGS_TRM_CBM.pdf`,
  `MISO-COORDINATED_FLOWGATES.pdf`) mirrored as dated source snapshots, with
  OATI's published webCARES root installed properly rather than the
  handshake pin (findings §6).
- **Crosswalk** per §4.1.

## 6. Pre-registered reopening conditions

Only these reopen the congestion component; each buys a **successor charter**
(with pre-registered bands/refutation criteria on the miso-76 template),
never a direct build:

- **RO-1 — MISO publishes the missing coefficients or a boundary-aligned
  limit:** shift factors/PTDFs for the coordinated-flowgate universe, or
  interface-defined limits with a declared boundary/generator mapping onto
  elements our reduced network carries (an ERCOT-GTC or CAISO-MIC analogue
  on a model boundary).
- **RO-2 — The owner charters the RP-6 physics-derived reduced-network
  program as its own lane**, accepting its scope (estimated impedances,
  disclosed; validation plan for the reduction) in that lane's charter.
- **RO-3 — Zone refinement that converts dominant flowgates into
  between-zone boundary elements** (e.g. a West or Plains split). Note the
  bar: it requires the same load-split unblocks that gate D1/D2 *plus*
  probe evidence that the refined boundary actually carries the congestion
  mass — at 6 zones the between-zone share is ≤ 0.8 %, and a split that
  does not move that number is RP-1 with more zones.
- **RO-4 — Publication of the hourly operationally derated limit series:
  does NOT alone reopen.** It upgrades the §4.3 cap-series choice within a
  successor charter opened by RO-1/2/3, but the representation block is
  independent of which limit series exists.

## 7. Freeze and sign-off terms

- The owner sign-off decision is a single question: **accept the NO-BUILD
  verdict and ledger entry** (this charter freezes as-is), or **override** by
  either selecting RO-2 (chartering the RP-6 program) or redirecting the
  MISO lane elsewhere (the open-lanes list in the miso-77/78 handoffs).
- On sign-off this charter freezes: §2 adjudications and §6 conditions may
  not be edited, only superseded by a successor charter citing a fired
  reopening condition or new external facts. §2's refutations bind successor
  charters (a successor may not re-admit RP-1–RP-5 without new external
  facts of the RO-1 class).
- Until sign-off: no intake, no derive, no crosswalk, no LP design in this
  lane (charter-first discipline; nothing in this session wrote any).

## 8. Ledger updates carried by this charter

- **miso-76 charter §3 M4 contingency: RESOLVED.** Fired (miso-77 GO on
  fetchability) → chartered here → NO-BUILD at representation. The miso-76
  wording "documented data-blocked limitation" is superseded by
  **data-blocked-at-representation** with §6 reopening conditions.
- **Documented-limitation ledger:** the congestion component of
  intra-Midwest separation beyond existing structure, and the East-internal
  ~75 % coverage gap, both stand as disclosed limitations of the MISO
  keeper line (currently `2026-07-18-miso-75-manitoba-meritcap`,
  determination NOT-YET, 2 fails — unchanged by this charter).
- **Out-of-scope restated:** C3a-2025/C3c tail; declined determination path;
  direction-symmetric losses; D1 Z2/Z7; `gas_daily_shape` interp; PJM
  merit-cap twin.
