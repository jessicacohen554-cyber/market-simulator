# PRECOMMIT — caiso-223: SUB-ZONAL TOPOLOGY PROGRAM, OPENING ROUND (scope + membership + LDF derivation; ZERO-SOLVE)

**Session** caiso-223 · **Date** 2026-08-30 · **Branch**
`claude/caiso-223-subzonal-scope-x5egla` · **Base** `97ab0a5` (main, post-def338e)

**Authority.** Owner ruling 2026-08-30 PM: caiso-222 Q2 route (iii) ARMED as a
chartered program opening round. Charter text:
`ASSESSMENT-caiso222-owner-sitting-2026-08-30.md` §(iii) (the honest scoping
note) + the Q2 ruling. Lineage: caiso-217 (crosswalk) / 218 (path-limit null +
identifiability kill) / 219 (deliverability null + census re-location) / 221
(surplus-design kill + §E attribution) / 222 (route census); the caiso-172
ATL_LDF precedent (measured Path-15 PG&E load split, zero free parameters).

**What this round IS and IS NOT.** A REPRESENTATION-GRAIN PROGRAM, NOT A LEVER
(caiso-221 §E(iii); caiso-222 §(iii) "a representation-grain program, not a
lever"). Nothing in this round arms, solves, scores, or registers anything.
The CAISO lane's terminal rest (caiso-201, mapped by caiso-222) is NOT
re-opened. The keeper stays `2026-08-26-caiso-220-c1-crosswalk` (NOT-YET on
C3a alone, C3c ledgered). No `ScenarioConfig` field is added — if execution
finds one is needed, the round STOPS and reports instead (charter order). No
mechanism-matrix row or cell verdict moves (nothing is proposed as a lever or
tested; rule-28 duties (a)–(d) do not fire). A future solve/arm round is a NEW
owner-visible charter — this document does not request one.

> **This document is pushed BEFORE any derivation runs.** The partition
> candidate space and decision criteria (§2), the membership tier ladder (§3),
> the LDF construction and its data acceptance gates (§4), and the
> sufficiency-statement obligation (§5) are fixed ahead of the derived
> numbers. Every §2 input is an ALREADY-COMMITTED byte (census JSON, atlas
> CSVs, crosswalk CSV/JSON, DMM element table in FINDING-caiso218 §B) — the
> partition adjudication consumes no number produced later in this round, and
> no step reads a model output or a residual [R-STRUCT, R-FROZEN-DERIVE].

---

## 1. Standing state, verified at this HEAD

* Keeper `2026-08-26-caiso-220-c1-crosswalk`: NOT-YET, C3a the sole
  load-bearing FAIL (+4.0 PASS / +12.5 / +15.5), C3c the single ledgered
  caveat, C1 12/12 free 8/8, DOF 11/7. In-model queue EMPTY; lane at the
  caiso-201 terminal rest with the caiso-221 §E + caiso-222 Q2 decision map.
* CAISO holds NO `complete`/`final` marker; the holdout spend freeze is
  ACTIVE (tier-scoped to locked_test). **This round runs ZERO solves and its
  reads stay inside 2023–2025** [R-HOLDOUT]. The Atlas reference reports are
  effective-dated reference data, not out-of-training market outcomes; the
  derivation day-weights them over calendar 2023/2024/2025 exactly as the
  caiso-172 keeper method does.
* Everything derived here is CAISO's [R-ISO-SCOPE].
* Committed evidence base (all pre-existing bytes, nothing re-surveyed):
  - `results/calibration/_caiso219_deliverability_census.json` — the
    93-constraint Attachment-A census with On/Off-Peak flags (off-peak mass:
    PG&E Fresno 14/19, PG&E Kern 7/10, SCE Northern incl. Tehachapi 2/8 with
    Tehachapi proper 0/3).
  - `FINDING-caiso218-path-limit-survey-2026-08-24.md` §B — the DMM element
    census with 2023-annual average binding limits and per-year binding
    windows; §C — the single-static-cut identifiability kill.
  - `data/raw/caiso-atlas/ATL_PNODE_MAP.csv` — authoritative TH_*_GEN pnode
    membership; `ATL_LDF.csv` — DLAP_PGAE per-pnode load distribution
    factors + the 15 `SLAP_PG*` sub-LAP pnode lists (committed caiso-172
    snapshots, 2023–2025 windows).
  - `data/raw/reference/caiso-plant-hub-membership.{csv,json}` — the
    caiso-217 generator-hub crosswalk (446 plants / 41.1 GW, pnode column
    included).
  - `data/raw/fleet-egrid/` + `data/raw/eia-860/` — plant county/lat-lon for
    the geographic fallback tier (the instruments `zone_assignment.py`
    already uses).
  - Attachment B2 (deliverability constraint boundary diagrams) —
    adjudicated by caiso-219 §B route 3 as "membership evidence only; carries
    no MW". It is NOT committed. §3 pre-registers one OPTIONAL fetch attempt
    for boundary corroboration; failure or illegibility is recorded, never
    blocking. This is a use of the object for its adjudicated purpose, not a
    re-survey of the caiso-218/219 walls (the caiso-222 §8.2 watch-test fence
    binds only limit-side wall re-checks and is untouched).

## 2. Deliverable 1 — the partition: candidate space and decision criteria (fixed ex ante)

**Criteria** (all four must hold for the proposed partition; the charter's
"out by construction" classes are restated as kills):

* **K1 (not the dead class).** A partition that reduces to the static
  single-link class — one internal cut with a static scalar — is OUT
  (caiso-218 §F.3: any future limit-side object must be year-varying +
  element-grounded, or sub-zonal). The proposal must let reality's
  year-varying binding geometry be expressed (different elements on different
  boundaries binding in different years).
* **K2 (element-grounded boundaries).** Every NEW internal boundary must be
  identified with named, committed-record elements (DMM census ids and/or
  census constraint rows), each with its side-of-boundary membership
  verifiable in `ATL_PNODE_MAP` at substation grain. A boundary with no
  citable element identity is not proposable.
* **K3 (off-peak census grounding).** The partition must put the census's
  off-peak constraint mass ON or INSIDE new boundaries: PG&E Fresno (14/19)
  and PG&E Kern (7/10) — the Gates–Midway complex. Tehachapi is 0/3 off-peak
  (caiso-219 §D): NO SP15-side cut is supported, and none is proposed.
* **K4 (membership + load derivable from committed instruments).** Every
  proposed sub-zone must have (a) a load definition derivable from the
  committed ATL_LDF/sub-LAP bytes by the caiso-172 method, and (b) a
  generator membership derivable from the committed crosswalk + atlas +
  county instruments with the unassignable mass enumerable. A sub-zone whose
  membership would require the CEII FNM is not proposable this round.

**Candidate space** (from the committed record; adjudicated in FINDING §A
against K1–K4 using only the §1 bytes):

| id | partition | sketch |
|---|---|---|
| P-A | NP15 → {NP15, FSNO}; ZP26 → {ZP26_COAST, ZP26_KERN} | valley pocket + coast/Kern split |
| P-A′ | NP15 → {NP15, FSNO}; ZP26 unchanged | single new valley-pocket sub-zone |
| P-B | one joint Fresno+Kern pocket spanning today's NP15/ZP26 boundary | Gates–Midway becomes pocket-INTERNAL |
| P-C | ZP26 → {ZP26_COAST, ZP26_KERN} only; NP15 unchanged | Kern-only split, Fresno belt stays diluted |

Pre-registered kill tests: P-B fails K3 by construction (Gates–Midway — the
named off-peak complex — becomes internal to the pocket and unrepresentable).
P-C leaves the LARGER half of the off-peak census mass (Fresno 14/19) and the
highest-frequency DMM binder (Moss Landing–Las Aguilas, 24 %/27 % of ALL
hours 2024/Q3-2025) invisible inside NP15 — it fails K3's Fresno leg. P-A vs
P-A′ turns on K2/K4 for the COAST↔KERN boundary: the committed record must
supply a named element separating the SLO coastal strip from the Kern/Midway
complex, and a load instrument that partitions them. §A adjudicates on the
committed bytes (known at precommit time: no census/DMM row names a
coast↔Kern element — Diablo Canyon's second 500 kV outlet is not in the
census — and `SLAP_PGZP` mixes coastal SLO pnodes with west-Kern-fringe
pnodes, so the sub-LAP instrument does not partition coast from Kern). If
both legs hold as stated, P-A fails K2+K4 and **P-A′ is the proposal**; the
FINDING states the adjudication with the bytes.

**Naming.** The new sub-zone, if P-A′ carries: `FSNO` (PG&E Fresno division
code style, matching `SLAP_PGF1`). Parent-lineage invariant: load shares
satisfy old-NP15-side ≈ NP15′ + FSNO and ZP26′ ≈ old ZP26 up to the measured
sliver reconciled in §4 G5.

**Link statements.** For each link of the proposed partition the FINDING
states: the element identities (constraint ids), the DMM binding record
per year (from caiso-218 §B), the DMM 2023 average binding limit scalars AS
EVIDENCE ONLY (the caiso-222 §(iii) "one thin path", admissibility
UNADJUDICATED — nothing is armed, no limit value is proposed for arming),
and what the boundary is FOR. The existing NP15↔ZP26 5,400 MW link's
disposition is stated explicitly.

## 3. Deliverable 2 — membership + crosswalk re-cut (method fixed ex ante)

Population: the caiso-217 crosswalk's 446 joined plants PLUS the pnode
universes of both atlas files. Outputs: a pnode→sub-zone map and a plant
re-cut table, both committed under the probe-artifact namespace
(`results/calibration/`), the same class as
`_caiso219_deliverability_census.json`. **No new on-disk DATATYPE is
produced** — nothing consumes these artifacts this round, so the data-intake
discipline (schema/clean-seam) is deliberately NOT spent; the future arm
round promotes them through it. [Charter's "if new on-disk datatypes are
produced" clause: not triggered.]

Assignment tiers (highest wins; each row carries its method tag; ties and
failures fall through, never majority-voted silently):

* **Load pnodes** (`DLAP_PGAE` universe): partition sub-LAP rule first —
  `SLAP_PGF1` → FSNO, `SLAP_PGZP`/`SLAP_PGKN` → ZP26 (their 100 %-ZP26
  membership is the committed caiso-172 finding); remaining nodes via the
  caiso-172 tiers (substation hub match, then sub-LAP dominant hub) → NP15 /
  ZP26; residue reported and excluded from normalisation.
* **Gen pnodes / plants**:
  1. hub from the committed crosswalk (or atlas membership for bare pnodes) —
     TH_SP15 plants keep their existing SP15-pocket assignment untouched;
     TH_ZP26 → ZP26 except the explicit Gates-complex substation claim
     (substation `GATES` — the boundary node itself, census "PG&E Fresno"
     area) → FSNO; TH_NP15 → tier 2.
  2. sub-LAP co-location: a TH_NP15 plant whose pnode substation hosts load
     pnodes of exactly one partition-relevant sub-LAP inherits its side
     (PGF1-co-located → FSNO; a non-partition sub-LAP → NP15). Ambiguous
     co-location (multiple sub-LAPs disagreeing on the side) falls through.
  3. county fallback (eGRID/EIA-860, the `zone_assignment.py` instruments):
     county ∈ {Fresno, Kings, Madera, Merced} → FSNO; any other county →
     NP15. The four-county set is the PGF1-division footprint as evidenced in
     the committed LDF bytes (Merced/Atwater/Huron pnodes in `SLAP_PGF1`)
     plus the census's own Fresno-area northern reach (Chowchilla/Le Grand/
     Merced rows); Tulare is EXCLUDED (SCE foothill cluster is TH_SP15 by
     crosswalk; PG&E Tulare fringe is `SLAP_PGZP` → ZP26-side).
  4. default: TH_NP15 with no evidence at tiers 2–3 stays NP15, COUNTED and
     reported as default-mass (the honesty duty — these are "right by
     default", not measured).
* **Unjoined plants** (no crosswalk row): existing geographic zone rule
  decides the hub-level zone as today; within old-NP15, the county tier (3)
  decides FSNO vs NP15; no-county plants stay NP15 and are counted.

**Witness set (pre-registered; all must land or the miss is reported in the
FINDING, never silently absorbed):** MUSTANG → FSNO; SCHLNDLR (Five
Points) → FSNO; HENRIETA/Henrietta → FSNO; Slate/American Kings (Kings co.)
→ FSNO; Helms PS (unjoined, Fresno co.) → FSNO via tier 3; GATES-connected
plants → FSNO; DIABLO / TOPAZ / CVSR → ZP26 (unchanged); MIDWAY-connected →
ZP26 (unchanged); MOSSLD / TESLA → NP15 (unchanged); ALTA (Tehachapi) →
SP15-side (unchanged); the caiso-217 witness gates that don't involve the
new boundary must reproduce unchanged.

**Optional corroboration step:** one fetch attempt of Attachment B2; if a
text layer yields the Fresno/Kern constraint boundary substation lists, they
are distilled to `_caiso223_b2_boundaries.json` and cited as membership
corroboration; if the PDF is image-only or unreachable, the gap is recorded
in §5's list. Not blocking either way.

## 4. Deliverable 3 — the sub-zonal LDF load split (construction + data gates fixed ex ante)

Method: the caiso-172 construction generalized from two buckets to the
partition's buckets, over the SAME committed Atlas snapshots
(`data/raw/caiso-atlas/`, no network, no re-fetch): assign each `DLAP_PGAE`
load pnode per §3's load rule, group the DLAP factors by bucket, day-weight
over every live effective window per calendar year 2023/2024/2025, exclude
the residue from normalisation, report it. Zero free parameters; the derive
reads no model output [R-MEASURED admissible: regenerates for any year from
published LDFs and responds to changed conditions; R-FROZEN-DERIVE: cites
source bytes only].

**Pre-registered DATA acceptance gates** (same family as caiso-172 §4; they
read no model output):

* **G1** — per-year day-weighted `DLAP_PGAE` LDF sum ≥ 99.99 (the factors
  partition the LAP).
* **G2** — unassigned residue ≤ 5.0 LDF points per year.
* **G3** — tier-1 substation-match support ≥ 300 nodes (backs the hub tiers
  for the non-partition remainder).
* **G4** — inter-year stability: |max−min| of each derived bucket share
  across 2023–2025 ≤ 0.010.
* **G5** — hub-level reconciliation: the derived buckets re-aggregated to
  the Path-15 hub sides must reproduce the committed caiso-172 split within
  |Δ| ≤ 0.010 of ZP26 0.116049 (the construction may move mass only via the
  documented PGF1↔hub-tier sliver; a larger move means the machinery, not
  the geography, changed).

A gate FAIL does not get patched silently: the FINDING reports it and the
artifact is marked non-consumable.

## 5. Deliverable 4 — the sufficiency statement (obligation fixed ex ante)

The FINDING ends with the honest gap list — pre-registered to include at
least: (a) link limits: CEII-walled (caiso-218/219; caiso-222 §(ii)); the
one thin non-reducing path (DMM 2023-annual element scalars) with its three
unwaivable qualifications restated and its rule-13/14 adjudication
DELIBERATELY NOT performed here; W-2/W-3 watch objects as the feeds that
would upgrade this grain; (b) the caiso-221 C-E load-share warning applied
to this partition's own load shares — what sub-zonal price separation can
and cannot move in the SCORED ISO-lw mean, stated with the partition's
derived shares; (c) membership sharpeners a future round needs (B2
extraction, the atlas's substation-coverage ceiling from caiso-217 §A);
(d) what the next round IS (a new owner-visible charter; not requested
here); (e) the caiso-218 §C design risk carried openly: single-vintage
static element limits may reproduce the split no better than the single cut
did — sufficiency untested and untestable without the program itself.

## 6. Deliverables and push discipline

1. This PRECOMMIT — pushed first, before any derivation runs.
2. `scripts/probes/_caiso223_subzonal_scope.py` — the probe (sections:
   A partition adjudication inputs, B membership re-cut, C LDF split,
   D controls/witnesses); deterministic JSON output.
3. `results/calibration/_caiso223_subzonal_scope.json` — every number;
   `_caiso223_membership_recut.csv` + `_caiso223_pnode_subzone_map.csv` —
   the membership artifacts; optionally `_caiso223_b2_boundaries.json`.
4. `results/calibration/FINDING-caiso223-subzonal-scope-2026-08-30.md` —
   partition statement (§A), membership (§B), LDF split (§C), sufficiency
   statement (§D), records/fences (§E).
5. `docs/calibration-log/caiso.md` caiso-223 entry (rebase on fresh main
   before pushing if the audit-rulings lane has appended).

Each pushed as produced (small commits, `git push` on a freshly-fetched
base; HTTP/1.1 retry per the standing recipe). No PR is opened; THE OWNER
MERGES. Off-limits surfaces honored: no capx-* file, no other lane's
artifacts, no keeper shard, no marker, no matrix shard edit.
