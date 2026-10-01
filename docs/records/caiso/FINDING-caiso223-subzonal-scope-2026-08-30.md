# FINDING — caiso-223: SUB-ZONAL TOPOLOGY PROGRAM, OPENING ROUND — the partition is PROPOSED AND ADJUDICATED (P-A′: one new San-Joaquin-Valley pocket zone FSNO between two element-grounded cuts, replacing the single Path-15 link that the DMM record says does NOT bind while the two cuts that DO bind are invisible at hub grain), its MEMBERSHIP is DERIVED (42 crosswalk plants / 2,701 MW into FSNO; pnode map committed; zero silent defaults), and its LOAD SPLIT is MEASURED (caiso-172 ATL_LDF method, 3-way: FSNO 0.1326 / ZP26 0.1148 / NP15 0.7526 of DLAP_PGAE, gates 13/13 PASS, two-way control EXACT vs the committed caiso-172 artifact) — ZERO-SOLVE; nothing armed; the sufficiency gap list ends the round (2026-08-30)

**Authority.** Owner ruling 2026-08-30 PM arming caiso-222 Q2 route (iii) as a
chartered opening round: scope + membership + LDF derivation, ZERO-SOLVE. A
REPRESENTATION-GRAIN PROGRAM, NOT A LEVER (caiso-221 §E(iii), caiso-222
§(iii)). **Keeper `2026-08-26-caiso-220-c1-crosswalk` UNCHANGED (NOT-YET on
C3a alone; C3c ledgered); the caiso-201 terminal rest is NOT re-opened; no
`ScenarioConfig` field, no solve, no registration, no matrix row or cell
move; reads stayed in 2023–2025** [R-HOLDOUT]. Method and gates were fixed ex
ante in `PRECOMMIT-caiso223-subzonal-scope-2026-08-30.md` (pushed before any
derivation ran).

Instruments (committed): `scripts/probes/_caiso223_subzonal_scope.py` →
`results/calibration/_caiso223_subzonal_scope.json` (+
`_caiso223_membership_recut.csv`, `_caiso223_pnode_subzone_map.csv`);
`scripts/probes/_caiso223_b2_extract.py` → `_caiso223_b2_boundaries.json`.
All read committed bytes only (census JSON, caiso-172 Atlas snapshots,
caiso-217 crosswalk, eGRID2023 + EIA-860 counties, the committed caiso-172
split JSON) plus the one pre-registered Attachment-B2 fetch; no model output,
no residual [R-STRUCT, R-FROZEN-DERIVE].

## THE ONE-SCREEN OWNER SUMMARY

* **The structural fact the partition rests on:** today's model enforces the
  one internal cut whose elements the DMM record does NOT show binding
  (Los Banos–Gates, the 5,400 MW Path-15 link), while the two cuts that DO
  bind are both INVISIBLE at hub grain — Tesla–Los Banos #1 500 kV (1,600 MW)
  + Moss Landing–Las Aguilas 230 kV (340 MW; **24 %/27 % of ALL hours
  2024/Q3-2025**, the record's highest-frequency binder) are TH_NP15-internal,
  and Gates–Midway #1 500 kV (2,500 MW; 90 % of 2023 congestion Sep–Dec) is
  TH_ZP26-internal (atlas anchors verified from committed bytes: TESLA/
  MOSSLD/LASAGUIL/PANOCHE = NP15-side; GATES/MIDWAY/DIABLO = ZP26-side).
* **The partition (P-A′):** one new zone — **FSNO**, the San Joaquin Valley
  pocket (Los Banos / Las Aguilas / Panoche / the Westlands–Kings solar belt /
  Fresno metro / the Gates complex) — between two NEW element-grounded links:
  NP15↔FSNO = {Tesla–Los Banos #1, Moss Landing–Las Aguilas} and FSNO↔ZP26 =
  {Gates–Midway #1, Diablo–Gates 500, Cal Flat–Gates 230, the Gates 500/230
  TBs}. Path 15 proper becomes FSNO-internal spine. ZP26/SP15/pockets/WECC
  unchanged (Tehachapi is 0/3 off-peak — no SP15 cut). Alternatives killed on
  the precommit criteria: a joint Fresno+Kern pocket makes Gates–Midway
  internal (K3); a Kern-only split leaves the larger Fresno census family
  (14/19 off-peak) and the highest-frequency binder invisible (K3); a
  coast/Kern split of ZP26 has NO committed element (Diablo Canyon's second
  500 kV outlet is absent from the census) and no partitioning load
  instrument — SLAP_PGZP mixes coastal-SLO with west-Kern-fringe pnodes (K2+K4).
* **Membership, measured:** the caiso-217 crosswalk re-cuts with ZERO silent
  defaults — FSNO takes 42 plants / 2,701 MW (solar 2,011, hydro 234 incl.
  the Kerckhoff/Kings-River Sierra-foothill fleet, batteries 184, gas ~271):
  3,011 MW of the TH_NP15 pool decided by sub-LAP co-location, 6,422 MW by
  county (1,661 MW of that via the EIA-860 fill for post-eGRID-vintage
  plants — Scarlet 590, Luna Valley 200, Kola/Proxima resolved to San
  Joaquin/Stanislaus → NP15 by their own EIA-860 counties), 0 MW default.
  Unjoined four-county mass enumerated: 5,336 MW / 116 plants on the
  eGRID2023 CISO base, **Helms PS (1,212 MW) among them → FSNO by county** —
  the pocket contains its own big absorber.
* **Load, measured:** the caiso-172 machinery generalized 3-way —
  **FSNO 0.132592 / ZP26 0.114794 / NP15 0.752614** of `DLAP_PGAE`
  (day-weighted 2023–2025; FSNO year-spread 0.0002). All 13 pre-registered
  gates PASS; the exact caiso-172 two-way replication reproduces the
  committed artifact **bit-for-bit** (0.116607/0.115536/0.116004), and the
  3-way ZP26 differs from it by only **0.001255** (G5 — the predicted
  PGF1-sliver). ISO-level (×0.4615 PG&E share, reporting only): FSNO ≈ 6.1 %,
  ZP26 ≈ 5.3 %, NP15 ≈ 34.7 %.
* **Sufficiency, honestly:** UNTESTED AND UNTESTABLE WITHOUT THE PROGRAM
  (caiso-222 §(iii), carried verbatim). The direct pocket-floor channel is
  bounded SMALL by the committed caiso-221 C-E arithmetic extended to the
  measured shares (§D.2: a static scaling illustration reaches only ≈
  −$0.23/−$0.32/−$0.25 lw vs required −$0.85/−$1.90) — the program's C3a
  case must rest on CHANGED SYSTEM DISPATCH (surplus trapped in FSNO reaches
  absorbers/exports differently), which only a chartered solve round can
  measure. Link limits remain CEII-walled; the one thin path (DMM 2023
  scalars) keeps its three unwaivable qualifications and its rule-13/14
  adjudication is deliberately NOT performed. **The ask: NOTHING** — the
  round ends at the gap list; a future solve/arm round is a NEW owner
  charter.

---

## §A — The partition, adjudicated (precommit §2 criteria, committed bytes only)

Controls first: the census control reproduces caiso-219 §D exactly (Fresno
off-peak 14/19, Kern 7/10, SCE Northern 2/8, Tehachapi rows 0/3 off-peak);
the atlas hub anchors land as stated (TESLA/MOSSLD/LASAGUIL/PANOCHE/SCHLNDLR
→ NP15; GATES/MIDWAY/DIABLO → ZP26; VINCENT/WIRLWIND → SP15).

**Adjudication against K1–K4** (`_caiso223_subzonal_scope.json` A.5):

| candidate | verdict |
|---|---|
| P-B (joint Fresno+Kern pocket) | **OUT — K3 by construction**: Gates–Midway #1 becomes pocket-INTERNAL; the complex the charter names becomes unrepresentable |
| P-C (Kern-only split) | **OUT — K3 (Fresno leg)**: the larger off-peak family (Fresno 14/19) and Moss Landing–Las Aguilas (24 %/27 % of ALL hours) stay invisible inside NP15 |
| P-A (P-A′ + coast/Kern split of ZP26) | **OUT — K2+K4**: no committed census/DMM row names a coast↔Kern element (Diablo–Midway is absent from the census), and `SLAP_PGZP` mixes coastal-SLO pnodes (ATASCDRO, BAYWOOD) with west-Kern-fringe pnodes (3EMIDIO, BELRIDGE, ARVIN, ALPAUGH) so the committed load instrument cannot partition them (name-geography recorded as corroboration; the operative kill is K2) |
| **P-A′ (FSNO only)** | **PROPOSED — passes K1–K4** (below) |

**The proposed topology** (machine-readable spec: JSON `A_partition.partition_spec`):

| object | statement |
|---|---|
| zones | NP15 (residual), **FSNO (NEW)**, ZP26 (scope unchanged: SLAP_PGZP+PGKN load; Kern/Midway complex + SLO coastal gen incl. Diablo/Topaz/CVSR), LA_BASIN, SDGE, SP15_rest, WECC_import — 7 zones, 6 load-carrying |
| **NP15↔FSNO (NEW)** | elements: Tesla–Los Banos #1 500 kV (`30040_TESLA_500_30050_LOSBANOS_500_BR_1_1`; DMM-2023 avg binding limit 1,600 MW; 2024: 6.5 % of hours, winter-heavy) + Moss Landing–Las Aguilas 230 kV (`30750_MOSSLD_230_30797_LASAGUIL_230_BR_1_1`; 340 MW; 2023 >70 % of congestion 9a–3p Apr–Oct; 2024 24 % of ALL hours; Q3-2025 27 %). Purpose: the valley-pocket ↔ Bay/coast cut — both elements TH_NP15-internal today |
| **FSNO↔ZP26 (NEW)** | element: Gates–Midway #1 500 kV (`30055_GATES1_500_30060_MIDWAY_500_BR_1_1`; 2,500 MW; 2023 >80 % of congestion 8a–3p, 90 % Sep–Dec; 2024 9 % of ALL hours HE9–15) + census boundary rows Diablo–Gates 500 kV (Off-Peak; Kern+Fresno), Cal Flat–Gates 230 kV (Off-Peak; Kern+Los Padres), Gates 500/230 kV TB #11/#12 (Off-Peak; the boundary complex's own transformers). Purpose: the Gates–Midway cut the charter names — the census's off-peak mass converges on this complex from both sides |
| ZP26↔SP15_rest (existing, 4,000) | element identities now stated: Midway–Vincent #2 500 kV (≈2,100 N→S; 50 % of 2023 congestion 5–8 pm Jun–Aug), `6410_CP1_NG` (1,600; protects Midway–Whirlwind for the Midway–Vincent #1+#2 contingency), and Midway–Whirlwind 500 kV — the TRTP Tehachapi trunk — terminating ON this boundary (WIRLWIND=TH_SP15 / MIDWAY=TH_ZP26, atlas) |
| **replaced** | the NP15↔ZP26 5,400 MW Path-15 link: Los Banos–Gates 500 kV and Panoche–Gates 230 kV #1/#2 (200 MW; 2023-Q1 binder) become **FSNO-INTERNAL spine** — consistent with the DMM record, in which Los Banos–Gates itself is not a top binder while the two chain cuts are |
| unchanged | WECC→NP15 (COI 4,800), WECC→SP15_rest (10,623), SP15_rest→LA_BASIN, SP15_rest→SDGE (LCT one-way caps) |

**K1 (escapes the dead class).** caiso-218 §C killed the single static cut on
identifiability: the recon's exceedance is strictly year-ordered at every X
while reality's split-hour vector is non-monotone. The chain replaces one
static scalar with two boundaries whose OWN elements bind in different years
and windows (Gates–Midway Sep–Dec 2023 vs 9 % HE9–15 2024; Moss Landing
dominant 2024/25; Tesla–Los Banos winter-heavy) — the year-varying geometry
becomes expressible ACROSS boundaries instead of unidentifiable within one.
Whether a static per-link limit VINTAGE suffices is a separate risk, carried
openly in §D (e).

**K2/K3/K4** — every new boundary element is atlas-anchored and named above;
the off-peak census mass sits on/inside the new boundaries (the Kern local
115/230 family is BELOW zonal grain and enumerated in §D, not forced into a
zone); membership and load derive from committed instruments (§B, §C).

## §B — Membership, derived (precommit §3 tier ladder; zero free parameters)

The 446-plant crosswalk re-cut (`_caiso223_membership_recut.csv`):

| sub-zone | plants | MW | note |
|---|---:|---:|---|
| **FSNO** | 42 | **2,701.2** | solar 2,011.3 / hydro 233.7 / battery 183.6 / gas_ct 184.8 / gas_other 49.6 / gas_cc 36.2 / biomass 2.0 |
| NP15 | 90 | 6,732.1 | residual TH_NP15 |
| ZP26 | 46 | 5,363.1 | unchanged incl. Diablo 2,323 / Topaz / CVSR (the GATES claim fired on 0 crosswalk plants) |
| SP15_side | 268 | 25,776.0 | untouched (hub:unchanged) |

FSNO by method: sub-LAP co-location (PGF1) 283.0 MW; county:Fresno 1,191.1;
county:Kings 991.3; county:Merced 203.0; county:Madera 32.8. The TH_NP15
pool honesty row: 132 plants / 9,433.3 MW = 3,011.4 slap-coloc + 6,421.9
county-decided (1,661.1 of it via the EIA-860 plant-sheet fill for
post-eGRID-vintage plants) + **0.0 default** — no plant was left "right by
default". The pnode map (`_caiso223_pnode_subzone_map.csv`, 3,680 rows)
covers the full atlas gen universe (2,008 pnodes: FSNO 60 / NP15 653 / ZP26
187 / SP15 1,108; 421 NP15 pnodes carry hub-default at pnode grain — no load
co-location; the GATES claim fires on 1 atlas pnode and 0 crosswalk plants)
and the `DLAP_PGAE` load universe (last 2025 window).

**Witness set (precommit §3): all substantive expectations land; two
name-fragment collisions resolved honestly, one 10 MW rule artifact
reported:**

* Mustang solar/battery (MUSTANGS, Kings) → FSNO ✓; the second "Mustang"
  match is **Mustang Hills LLC** — Alta-complex Tehachapi WIND at ALTA1G,
  correctly TH_SP15 unchanged (collision, not a miss).
* Five Points/SCHLNDLR → FSNO ✓; Slate → FSNO ✓; American Kings → FSNO ✓;
  Henrietta Peaker (98 MW) → FSNO ✓.
* **Henrietta D Energy Storage (10 MW, Kings co.) stays ZP26**: its measured
  hub is TH_ZP26 (`HENRTA_7_N002`) and the precommitted ladder lets TH_ZP26
  into FSNO only at the GATES substations. A pocket-interior TH_ZP26
  substation beyond Gates is exactly the class the ladder cannot see —
  REPORTED, not patched (§D (c) sharpener). 10 MW; immaterial.
* Diablo Canyon / Topaz / CVSR → ZP26 unchanged ✓; Moss Landing / Tesla →
  NP15 ✓; Alta → SP15 ✓; Helms → FSNO via county (enumeration level) ✓.

**Unassignable/default mass, enumerated:** crosswalk-side default = 0. The
unjoined remainder (no crosswalk row): 1,132 plants / 48,720 MW on the
eGRID2023 CISO base (stated vintage; NOT the model member-fleet denominator),
of which the four-county cohort — the mass whose sub-zone falls to the county
tier at arm time — is **116 plants / 5,336 MW incl. Helms (Fresno)**. The
caiso-217 §A atlas substation-coverage ceiling (17.3 GW of known-resource
substations absent from the hub list) is inherited unchanged by any sub-zonal
grain.

**Attachment B2 (pre-registered optional step)** — fetch SUCCEEDED (108-page
08/28/2024 revision, sha256 recorded in `_caiso223_b2_boundaries.json`):
the per-constraint diagram inventory corroborates the Attachment-A census
1:1 at diagram grain for Kern (pp. 79–88) and Fresno (pp. 90–108), with one
naming delta recorded (B2 "Q1959 SS–Gates 230 kV" vs census "Gates–Arco 230
kV"). **But every PG&E Kern/Fresno constraint page is RASTER-ONLY** (title +
images, no vector text), so the DFAX-circle substation lists for the proposed
boundaries are NOT text-extractable; the SCE-side control (Windhub page:
Windhub/Whirlwind/Pastoria/Vestal/Magunden labels) proves the extractor
works where text exists. Recorded as the §D (c) membership sharpener. No
limit, rating, or MW was read [caiso-218/219 fences].

## §C — The load split, measured (caiso-172 method, 3-way; gates 13/13 PASS)

Helpers imported from the frozen `derive_caiso_path15_load_split.py` so the
construction is provably shared; partition sub-LAPs first (PGF1→FSNO,
PGZP/PGKN→ZP26 — the caiso-172 100 %-ZP26 finding), caiso-172 hub tiers for
the remainder, residue excluded from normalisation and reported:

| year | FSNO | ZP26 | NP15 | residue pts | windows |
|---|---:|---:|---:|---:|---:|
| 2023 | 0.132613 | 0.115350 | 0.752036 | 2.473 | 6 |
| 2024 | 0.132682 | 0.114282 | 0.753036 | 2.152 | 8 |
| 2025 | 0.132480 | 0.114749 | 0.752771 | 2.153 | 6 |
| **mean** | **0.132592** | **0.114794** | **0.752614** | | |

Gates: G1 LDF sum 100.000 ✓×3; G2 residue ≤5.0 ✓×3; G3 tier-1 support
483/488/492 ≥300 ✓×3; G4 spreads FSNO 0.0002 / ZP26 0.0011 / NP15 0.0010 ≤
0.010 ✓×3; G5 |ZP26₃way − 0.116049| = 0.001255 ≤ 0.010 ✓. **Control:** the
exact caiso-172 two-way replication run in the same process reproduces the
committed `CAISO_path15_load_split.json` **exactly** (0.116607 / 0.115536 /
0.116004; mean 0.116049). ISO-level composition (× the 0.4615 PG&E TAC
share; REPORTING ONLY, nothing armed): FSNO 0.061191 / ZP26 0.052977 / NP15
0.347332. Rule-13 admissibility is the caiso-172 keeper input's own:
regenerates for any year from published LDFs; responds to changed conditions
(Fresno-division vs Bay-Area load growth moves it); reads no residual.

## §D — THE SUFFICIENCY STATEMENT (the honest gap list that ends the round)

Pre-registered obligation (precommit §5). Sufficiency of this partition for
C3a is **untested and untestable without the program itself** (caiso-222
§(iii), carried verbatim). What a future solve round still needs, and what
this round's own numbers add to the honesty of that list:

* **(a) Link limits — the walled half.** Every new link needs a limit and
  the limit class is CEII (FERC-715 / CRR-FNM / branch ratings; caiso-218
  route 7, caiso-219 route 5, caiso-222 §(ii) access classes A-1/A-2 with
  their two structural costs). The ONE published exception stays the DMM
  2023-annual element scalars now sitting on this partition's boundaries
  (1,600 + 340 at NP15↔FSNO; 2,500 at FSNO↔ZP26; ≈2,100 + 1,600 at
  ZP26↔SP15) — **admissibility UNADJUDICATED, and deliberately not
  adjudicated here**, with the three unwaivable qualifications carried:
  single vintage (2023 only — 2024/Q3-2025 DMM print no MW), top-congestion
  elements only (parallel unrated elements share each boundary: Diablo–Gates
  and Cal Flat–Gates at FSNO↔ZP26 — the rule-14 parallel-path misalignment),
  and the caiso-218/219 fences walling these scalars as intake. The watch
  feeds that would upgrade the grain: **W-2** (a limit/flow column appearing
  in `PRC_NOMOGRAM`/`PRC_CNSTR`/`PRC_RTM_FLOWGATE` — feeds exactly these
  elements) and **W-3** (a future DMM vintage printing MW); W-1 (path-BG
  re-enforcement) would resurrect the single-cut object instead, which the
  caiso-218 §C kill says is insufficient regardless.
* **(b) The load-share warning, updated with this round's measured shares.**
  caiso-221 C-E bounded whole-ZP26-at-floor at −$0.107/−$0.147/−$0.114 lw
  (ZP26 ≈ 5.0–5.2 % of load). A static load-share scaling of that committed
  bound to FSNO+ZP26 (0.0612+0.0530 ≈ 2.2× the base) illustrates ≈
  **−$0.23/−$0.32/−$0.25** — against required −$0.85 (2024) / −$1.90 (2025),
  the DIRECT pocket-floor channel alone is ~2.7×/7.6× short (an
  illustration, not a measurement: static shares scaled onto a committed
  bound). The program's C3a case therefore rests on **changed system
  dispatch** — surplus trapped in FSNO reaching storage/hydro/exports
  differently, altering south-wide price formation — which no pre-solve
  arithmetic can size. This is the honest version of "sufficiency
  untestable": the partition buys the REPRESENTATION the caiso-221 §E.1
  attribution requires (the sub-zonal constraint between southern supply and
  southern absorbers — Helms and 184 MW of batteries now sit INSIDE the
  pocket with 2.0 GW of its solar), not a promised number.
* **(c) Membership sharpeners.** The B2 PG&E boundary pages are raster-only
  (§B) — the DFAX substation lists need image-grain extraction or a CAISO
  ask; pocket-interior TH_ZP26 substations beyond GATES (the 10 MW
  Henrietta-D case) need exactly that instrument; the atlas substation
  ceiling (caiso-217 §A, 17.3 GW) and the eGRID-vintage county ceiling
  (worked around via the EIA-860 fill this round) are inherited; the
  unjoined four-county cohort (5,336 MW incl. Helms) rides the county tier
  until a finer instrument exists.
* **(d) What the next round IS** (a NEW owner-visible charter, not requested
  here): the limit-side rule-13/14 adjudication with its own precommit;
  topology/config implementation (zones+links+`CAISO_TAC_ZONE_WEIGHTS`
  3-way, `validate_topology` invariants, the fleet FSNO carve promoted
  through the data-intake discipline); re-validation of every armed CAISO
  mechanism at the new grain (RA must-offer, storage shape anchor, spill,
  deliverability seam) and full-span rule-16 re-solves — the caiso-222
  §(iii) cost class, unchanged.
* **(e) The design risk, carried openly** (caiso-218 §C): reality's binding
  geometry is year-varying and outage-driven; the chain makes it EXPRESSIBLE
  across two boundaries, but single-vintage static per-link limits may still
  reproduce the split no better than the single cut did. If the arm round
  proceeds on static scalars, this risk is its first pre-registered
  falsifier, and the backcast-admissible outage-overlay channel
  (transmission outages driving derates) is the structural escape it should
  examine — TODAY UNPUBLISHED for these elements (caiso-218 §F.3), so it is
  a watch item, not a plan.
* **(f) Below-zonal structure, excluded honestly.** The Kern local 115/230
  family (7 off-peak census rows: Semitropic–Midway, Kern–Tevis–Stockdale–
  Lamont, Midway TB #3, …) strands individual plants/clusters INSIDE ZP26 at
  grain finer than any defensible zone — representing it would need
  plant-cluster constraints, a different object class this program does not
  propose.

## §E — Records, disposition, fences (rule 28b — CAISO artifacts only)

Committed by this session (branch `claude/caiso-223-subzonal-scope-x5egla`,
each pushed as produced): the PRECOMMIT; the two probes; the four artifacts
(`_caiso223_subzonal_scope.json`, `_caiso223_membership_recut.csv`,
`_caiso223_pnode_subzone_map.csv`, `_caiso223_b2_boundaries.json`); this
FINDING; the `docs/calibration-log/caiso.md` caiso-223 entry.

**Matrix disposition:** NO row, NO cell move, NO §5.2 block — no
`ScenarioConfig` field exists, nothing was proposed as a lever or tested
(rule-28 duties (a)–(d) do not fire), and the charter pins the lane's other
record surfaces to the in-flight audit-rulings session; this FINDING + the
log entry are the round's record. **Filed items unchanged** (4 standing;
9 — the CEII wall, whose caiso-222 Q2 decision map this round now gives a
concrete consumer: the §A partition is what route-(ii)/W-2 data would feed).

DO-NOT-REDO additions (append to the caiso-202 §I / 215 §I / 216 §I / 218 §F
/ 219 §F / 220 §E / 221 §G / 222 §8 chain):

1. **Never re-adjudicate the P-A/P-B/P-C kills absent NEW committed
   evidence.** A coast↔Kern split of ZP26 needs a committed element identity
   (e.g. Diablo–Midway appearing in a census/DMM/B2-extractable record) and
   a partitioning load instrument — not a re-argument over the same bytes.
2. **Never re-attempt text extraction of the B2 08/28/2024 PG&E pages** —
   they are raster-only (sha256 recorded). A NEW revision, an image-grain
   program, or a CAISO ask are the only paths to the DFAX substation lists.
3. **Nothing in this round is an armable limit.** The DMM scalars on these
   boundaries stay evidence-only until a chartered rule-13/14 adjudication
   with its own precommit (restating caiso-218 §F.2/219 §F.2 at the new
   grain); the caiso-222 §8.2 watch tests remain the only sanctioned wall
   re-checks.

Keeper, markers, holdout freeze (no out-of-training year touched or read),
DOF ledger, every matrix cell, every bench part, and every source file other
than the §E additions: **UNCHANGED**. The lane REMAINS at the caiso-201
terminal rest; this round is representation prep filed against the caiso-222
route-(iii) map. THE OWNER MERGES.

**Next number: caiso-224.**
