# FINDING — ercot-234: the sub-zonal admissible-data SURVEY, and what it surfaced — **`NE_LOB` IS NOT A NORTHEAST-TEXAS CONSTRAINT.** The keeper's measured-GTC overlay carries a geographic mis-attribution (rule 14), carded to the owner as card Z

**Date:** 2026-08-24 · **ISO:** ERCOT · **Keeper (untouched):**
`2026-08-24-231-tie-zone-measured` (`results/calibration/ercot231_tiegtc_full`)
· **Authorization:** the card-Y RESOLUTIONS (Y-C — lane open; an open lane
"works its named-unmeasured objects or waits for new evidence") + the ercot-234
handoff's priority A: the sub-zonal admissible-data survey named by
`docs/FINDING-ercot233-nelob-timing-phase0-2026-08-24.md` §3.
· **Companion card:** `docs/DECISION-CARD-ercot234-nelob-identity-repair-2026-08-24.md`
(card Z, AWAITING OWNER SIGNATURE — nothing is repaired in this session).

**NO SOLVE, NO LP, NO MECHANISM BUILT OR TESTED, NO `ScenarioConfig` FIELD, NO
RUN REGISTERED, NO MATRIX CELL VERDICT (rule 28(b) not engaged), KEEPER
UNCHANGED, ZERO FITTED SCALARS.** This session performed documentary and
descriptive reads only: public ERCOT publications (fetched live 2026-08-24)
and the already-committed NP6-86 archives. No bar-bearing statistical
adjudication was run, so no precommit was owed; the one adjudicable claim in
part II is a documentary identity fact, quoted from ERCOT's own definitions.

---

## PART I — the chartered survey: what ERCOT publishes at ELEMENT grain

The question (FINDING-ercot233 §3): does any ERCOT publication provide
**element-grain, rule-13-admissible DRIVER data** (planned transmission outage
schedules, element ratings, constraint composition) that could re-open the
sub-zonal timing route? Surveyed live against ercot.com / EMIL on 2026-08-24:

| # | object | product | classification | verdict |
|---|---|---|---|---|
| 1 | Planned transmission outage schedules | **NP3-157-CD** "Consolidated Transmission Outage Report" (reportTypeId 13446), wrapping NP3-150-CD (withdrawals), NP3-424-CD (proposed), NP3-754-CD (approved/accepted), NP3-755-CD (rejected) | **SECURE + ECEII** — digital-certificate roles (`ICE_E_ADMIN_ECEII`, `MDT_G_VIEW`, `ICE_M_VIEW_ECEII`); the Outage Scheduler itself is MIS-secure | **NOT PUBLIC** |
| 2 | Element ratings | Network Operations Model (+ dynamic-ratings forms, TSP-side); no element-grain public ratings product found in EMIL | secure / CEII-class | **NOT PUBLIC** |
| 3 | GTC composition + GTLs | **NP3-770-M** "Generic Transmission Constraints Methodology" — the link ERCOT's own ROS slides give is `mis.ercot.com/secure/…` | **SECURE** (identity/purpose info IS public via workshop/ROS decks — see part II) | element-level time series NOT public; **identity public** |
| 4 | Constraint Management Plans | Nodal Protocols / Operating Guides objects; no public per-event schedule product found | — | methodology only, no time series |
| 5 | SOL methodology | PG7-225-M | public | methodology only |
| 6 | Element-level BINDING record | NP6-86-CD (committed, `data/raw/iso-specific-transmission`) | public | an **OUTCOME** — target only, never a driver (rule 13) |

The resource-side outage products that ARE public (NP3-161-CD, NP1-346-ER,
NP3-233-CD) carry generation-resource capacity, not transmission elements.

**Survey verdict: NO public, rule-13-admissible sub-zonal DRIVER source
exists.** The FINDING-ercot233 §3 reopen condition ("genuinely sub-zonal
admissible data") is not met by any public ERCOT product; meeting it would
require secure-MIS access (a market-participant credential + ECEII terms) —
an owner-level acquisition decision, not a data-intake this repo can perform.
The ercot-233 zonal-grain closure and the §10/ERCOT-117
`internal_congestion_split` `G` therefore STAND, un-reopened. (Also
re-verified in passing, unchanged from the corpus README: the ERCOT Data
Portal historical archive is login-gated behind bot protection, and
`api.ercot.com` needs an OAuth credential this environment does not hold.)

## PART II — what the identity check surfaced: `NE_LOB` is the Rio Grande Valley's corridor, not the Northeast-Texas lobe

Adjudicating admissibility for object 3 required reading the public GTC
identity record. That record contradicts the keeper's crosswalk.

### II.1 What ERCOT says NE_LOB is

ERCOT GTC Workshop, "Current Generic Transmission Constraint Definitions"
(Chad Thompson, 2020-02-24,
`ercot.com/files/docs/2020/02/21/III.A_Generic_Transmission_Constraint_Definitions_GTC_Workshop_02242020.pdf`):

> "The North Edinburg to Lobo GTC … represents a stability limit associated
> with **South Texas wind farms** connecting along the North Edinburg – Lobo
> 345 kV line. The interface name … in the Network Operations Model is
> '**NE_LOB**'."

North Edinburg (Hidalgo County, Rio Grande Valley) → Lobo (Webb County, near
Laredo). The same deck defines a SEPARATE **"East Texas GTC … a voltage
stability limit associated with flows out of the East Texas area … 'EASTEX'"**
— i.e. the actual export constraint of the Tyler/Longview/Texarkana lobe.

Still true in the keeper years: ERCOT's ROS GTC update (July-2024 deck,
`ercot.com/files/docs/2024/07/10/05-gtcupdate_ros_july2024.pdf`) groups it
under "**Valley Area GTC update** — Valley Export (VALEXP), NorthEd_Lobo
(NE_LOB), and NelsonSharpe_RioHondo (NELRIO)", updated for the
Lobo–Cenizo–…–North Edinburg second-circuit 345 kV work.

### II.2 What the model does with the name

- `constants.py::ERCOT_GTC_LINK_MAP` maps `"NE_LOB": [(("Northeast","North"), 1.0)]`,
  glossing it "Northeast Texas export lobe", and cites "The Use of GTCs in
  ERCOT (July 2020) for the GTC definitions" — a paper that does not define
  NE_LOB at all (verified: zero occurrences of NE_LOB/Edinburg/Lobo in its
  text). The definitions deck above, which does, contradicts the gloss.
- `iso_configs._ercot_config` carves the **Northeast zone out of North
  expressly "to capture the NE_LOB generic transmission constraint"** and sets
  the Northeast→North static export `ttc_mw=1300.0` from NE_LOB's measured
  limit-at-bind. This static rating is **not backcast-only — it is the
  forecast topology's East-Texas interface rating too.**
- The keeper arms `ercot_gtc_limits_measured`, so `data/gtc.py` overlays
  NE_LOB's measured HOURLY limits onto Northeast→North in every solved year;
  the same map routes `derive_ttc_limits.py` and `transmission_expansion.py`.
- Meanwhile the comments dismiss **EASTEX — the constraint that actually
  bounds the model's Northeast boundary — as an "intra-zone" GTC with "no
  representable link in this topology"**, the exact inverse of the truth: the
  model's own zone map places the Rio Grande Valley INSIDE its South zone
  (`zone_assignment.py` — "South (the coast and Rio Grande Valley)"), so
  NE_LOB is the unrepresentable intra-South pocket (VALEXP's class), and
  EASTEX is the representable one.

### II.3 The committed record's own numbers (NP6-86, GTC rows)

| year | NE_LOB active / binding intervals | NE_LOB limit p50 (MW) | EASTEX active / binding | EASTEX limit p50 (MW) |
|---|---|---|---|---|
| 2023 | 41,494 / 23,816 | 1,245 | 1,821 / 828 | 2,537 |
| 2024 | 26,934 / 11,435 | 1,260 | 443 / 191 | 1,909 |
| 2025 | 30,560 / 12,049 | 1,549 | 6 / 3 | 43,274 |

The keeper caps its ~8 GW Northeast lobe at the Valley corridor's
1,245–1,549 MW series and reproduces Valley-scale binding (model 1,974
congested h in 2023, per ercot-232) — while the real East Texas export
constraint bound **828 → 191 → 3** intervals, at roughly double the limit,
and in 2025 was parked effectively unconstrained (limit p50 43 GW). The 21
spurious in-season mid-band hours the ercot-231 promotion accepted (G-SPUR)
are, per ercot-232, exactly hours where this manufactured NE congestion
prices the Northeast zone $24–126 apart.

### II.4 What this re-reads — and what it does NOT re-open

- **The ercot-232/233 measured records STAND as measured.** Their target
  constructions compared the model's NE-lobe congestion against the measured
  NE_LOB series; every number is reproducible. What changes is the physical
  reading: the "timing is ~uncorrelated" result (corr −0.042), the
  "capability physics runs BACKWARDS" result (d2/d3 AUC 0.436/0.415), and
  the "tie placement carries zero timing information" result (d4 Spearman
  −0.0006) are all the EXPECTED outcome of scoring Northeast-Texas drivers
  against a **South-Texas** constraint's binding record. The mis-identity is
  the parsimonious root cause the ercot-233 closure lacked.
- **The ercot-233 closure is not re-opened** — all four zonal-grain drivers
  still close; there is nothing to re-test at that grain. After a repair
  there is no NE_LOB timing object at all: the model would no longer carry
  that series anywhere.
- **§10/ERCOT-117 `internal_congestion_split` `G` is not re-opened** — the
  repair is a crosswalk correction on the EXISTING topology, not a zone
  split; real NE-Texas element congestion remains sub-zonal and publicly
  unreachable (part I).
- **The ercot-231 tie placement is not re-opened** (ercot-232 adjudicated it
  counter-indicated to refine; Monticello genuinely sits in NE Texas).
  **ERCOT-76's import-side envelope is untouched** — it was derived from
  EAST-weather-zone load and CAMPD NE-plant output, genuinely Northeast data.
- **Q-B and R-A are untouched.** This is not a C3a/C3b-2023-targeted round:
  the object is a rule-14 `[R-ACCURATE]` mis-attribution in a measured input
  (and a rule-1 structural fidelity defect in the forecast topology),
  discovered from primary sources, not from the residual. Any 2023-price
  movement under a repair is side-effect-reported, per the standing fences.

### II.5 Consequence

A knowingly mis-attributed measured input may not simply rest (rule 14), and
its repair changes keeper inputs in all three years — so the decision is the
owner's: **card Z**
(`docs/DECISION-CARD-ercot234-nelob-identity-repair-2026-08-24.md`), which
proposes the crosswalk repair charter (NE_LOB out as an intra-South pocket;
EASTEX in at Northeast→North; static rating re-derived; full rule-16 3-year
re-solve under precommitted gates). Nothing is executed without a signature.

## Hygiene

Read-only session: public-web documentary reads + descriptive reads of the
committed `SCEDBTCNP686_*.parquet` archives (years ⊂ {2023, 2024, 2025},
rule 22; ERCOT-only, rule 25). No probe JSON (no bar-bearing measurement was
run). No CI job, no workflow. The pending **ercot-225 G-SPUR band-top gate
card remains OPEN as put** (AWAITING SIGN-OFF since 2026-08-21), independent
of card Z. Matrix duties: no cell verdict minted (28(b) — nothing tested);
the §5.1 head carries this session's blockquote.
