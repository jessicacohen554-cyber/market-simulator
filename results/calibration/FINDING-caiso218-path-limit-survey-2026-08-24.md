# FINDING — caiso-218: THE PATH-15/26 MEASURED OPERATING-LIMIT PHASE-0 SURVEY — a DECISIVE NULL at the cut grain (CAISO discontinued the internal-path limit as a market object on 2018-11-01), element-grain limits published only as DMM annual scalars, and the bounding what-if proves NO static cut limit — measured or otherwise — can reproduce reality's split-hour year pattern (2026-08-24)

**Authority:** owner 2026-08-23 ("give handoff prompt for a new suggestion to
continue work on calibration tuning for rubric failures") — this session is
the chartered Phase-0 continuation on the C3a failure via the caiso-216 §F.3b
fenced contingency (published operating limits ADMISSIBLE; realized-flow caps
NOT). NO LP, NO SOLVE, nothing armed, nothing registered, no cell verdict
moves. The caiso-201 rest is undisturbed; the queue stays EMPTY; this lever
was off-queue under the pre-stated fence.

**The one-line verdict:** the chartered object — a citable REAL-TIME operating
limit series for internal Path 15 / Path 26, 2023–2025 — **does not exist in
any public record**, because CAISO removed the internal path branch groups
from the market on 2018-11-01; and the committed bounding what-if
(`_caiso218_limit_whatif.json`) shows that even if a measured static/seasonal
cut limit existed, **no single value can reproduce reality's split-hour year
vector** — the lever class itself is measured insufficient. Per the charter,
"nothing citable exists" is decisive: **no intake is proposed, no solve is
asked, NOT-YET stands** (owner ruling 5), and the residual attribution
tightens onto the caiso-216 §F.3a gen-pocket/strandedness lane with measured
weight (§C, §D).

---

## §A — Standing state at MY HEAD, and the caiso-217 registration gap

The handoff's standing-state block describes a keeper
(`2026-08-23-caiso-217-crosswalk`, C3a +4.0/+12.5/+15.5, C3b
0.100/0.177/0.180, a filled caiso-217 §D–§G) that **never landed**. Verified
against `main` (c9a07b9), every remote branch, and the closed-PR record:

* The caiso-217 session's last landed commit is `6132867` (PR #4230,
  2026-08-23 19:58 UTC) — a mid-solve checkpoint holding only the 2023
  hourly sidecars. Its Phase A (crosswalk intake, `f0dd328`), FINDING draft
  §A–§C and the §B realized-membership JSON (`5b70419`) are committed; its
  completed solve, gates, determination, registration, keeper promotion, log
  entry, matrix stamps, and `_caiso217_zonal_decomp.json` are NOT — the solve
  completed only inside the lost container, and its numbers survive only as
  the caiso-218 handoff text (SECONDARY evidence, never committed
  measurement).
* **At HEAD the keeper is `2026-08-17-caiso-200-h1-memberpanel`** (NOT-YET,
  rubric v3.4, C3a the sole load-bearing FAIL at +4.1/+12.8/+15.7, C3c the
  single ledgered caveat, C1 12/12 free 8/8, DOF 10/7, no
  `complete`/`final` marker, freeze ACTIVE) and **the committed C3b baseline
  is 0.098/0.179/0.182** (caiso-209 correction; caiso-213 re-verification).
  Any future gate table cites THESE, not the handoff's caiso-217 values.
* The gap record is written into the caiso-217 FINDING (its §D–§F
  placeholders replaced by the honest account, same commit series as this
  FINDING), and the repair is FILED, not executed: the run's outputs are
  unrecoverable, so the only repair is a re-solve — at HEAD exactly a
  `caiso200_h1_memberpanel` replay, because the crosswalk entered as data
  and is active for every new CAISO solve — which remains owner-funded
  under the caiso-201 rest (§E).

What this session builds on is therefore exactly the COMMITTED post-crosswalk
state: `_caiso217_realized_membership.json` (bound hours 121/480/742 over the
armed 5,400 MW Path-15 S→N rating; reality split hours 1,310/1,691/1,347) —
not re-measured, and reproduced exactly by this session's probe controls (§C).

## §B — The survey table (Phase-0 deliverable 1)

Every route walked, with live fetch tests through the session proxy
(2026-08-24 UTC; scratch CSVs verified by row counts and column censuses).
Grain/span/alignment/fetchability per the caiso-172 pattern; **walls in
bold**.

| # | route | object & grain | span / retention (tested) | boundary alignment to our 2 internal links | fetchability | verdict |
|---|---|---|---|---|---|---|
| 1 | OASIS `TRNS_USAGE` / `TRNS_ATC` (+`TRNS_CURR_USAGE`) | per-TI per-direction HOURLY rating stack — `TRNS_RATING_OTC`, `_TTC`, `_TRM`, `_CBM`, `_CONSTRAINT`, `RATING_ATC` (the exact instrument type the packet wanted) | LIVE; serves 2023-06-15, refuses 2023-01-15 (ERR 1000) — the ~39-month rolling ageout (LMP-family boundary 2023-04-22 measured 2026-08-04, sliding daily); `TRNS_CURR_USAGE` current/future trade days only by design | **TI universe = 56 boundary interties/ISLs (live census, trade date 2025-06-02): ZERO internal paths** | proven (5.4 MB day-pull, 34,944 rows) | **WALLED — right instrument, wrong universe** |
| 2 | Path 15 / Path 26 TTC/ATC posting itself | the pre-2018 per-path TTC/ATC record | **DISCONTINUED effective 2018-11-01** — CAISO notice "TTC and ATC for Path 15 and Path 26 No Longer Available, effective 11/01/18": the ISO stopped calculating/posting them because it **no longer enforces the internal Path Branch Groups** (notice URL now 404s; substance corroborated by the search-indexed notice text and independently by tests: explicit `ti_id=PATH15_BG`/`PATH26_BG` queries return ERR 1000, and the July-2024 FNM "Intertie Constraint (ITC) and Branch Group (BG) Information" reference document — all 16 pages read — carries a complete ITC/BG census with NO Path 15/26 entry) | n/a — the market object was removed | n/a | **DEAD for 2023–2025** |
| 3 | OASIS `TRNS_OUTAGE` | per-TI outage events with `CURTAILED_OTC_MW` — a true curtailed-operating-limit derate record, event grain, 31-day query cap | LIVE (2,580 rows in the day sample) | universe = the same TIs **plus `PATH_WOR`** (West of River) and `CASCADE_BG` — named path objects CAN appear, but Path 15/26 do NOT | proven | **WALLED — right shape, wrong universe** |
| 4 | OASIS constraint shadow-price family — `PRC_NOMOGRAM`, `PRC_CNSTR`, `PRC_RTM_FLOWGATE` (+MPM/CD variants) | per-constraint hourly/5-min SHADOW PRICES; the nomogram id census DOES carry the real internal corridor (live day-list includes branch constraints whose `CONSTRAINT_CAUSE` is "PG1 GATES-LOSBNS_1 500", "PG1 MOSSLD-LOSBNS 500") | LIVE; serves 2023-06-15 (same retention family) | constraint-name grain = the corridor's real elements | proven (columns checked live: **no limit, no flow field** — spec v5.1.1 concurs) | **WALLED as intake — outcomes only** (inferring a cap from binding hours is the outcome pin the fence pre-forbids); ADMITTED as diagnostic evidence |
| 5 | DMM annual/quarterly Reports on Market Issues and Performance | the corridor's REAL constraint census with binding frequency, windows, and — 2023 annual only — **published average binding limits** (annual scalar, element grain) | 2023 annual (Jul 2024), 2024 annual (Aug 2025), Q3-2025 (Dec 2025) fetched & greppped in full | **element grain, NOT cut grain** — converting element limits to our single-link cut needs FNM shift factors (restricted/CEII) or realized flows (forbidden) | proven (PDFs) | **WALLED as intake; anchors the §C what-if and the §C/§D attribution** |
| 6 | `ENE_SLRS` (the handoff's "ATC record?" candidate) | system load & resource SCHEDULES | — | schedules are market outcomes, not limits | — | **adjudicated NO — not a limit record** |
| 7 | static/seasonal documents — WECC Path Rating Catalog (the armed source), ATC Implementation Document + tariff Appendix L-1 (methodology; "posted paths" = interties only), nomogram/path operating procedures (methodology, no series), CRR FNM (CRR-participant registration, restricted), FERC 715 (CEII) | static ratings / methodology | current | already reflected in the armed catalog ratings | mixed | **no RT series anywhere in the class** |
| 8 | non-OASIS daily transmission-outage postings | none exist publicly — the daily CNOG report (committed corpus) is GENERATORS; public transmission-outage visibility IS route 3 | — | — | — | **closed** |

**The census behind the wall (route 1, recorded for future sessions):** the
live 2025 TI universe is `ADLANTO-SP_ITC … WSTWGMEAD_ITC` (56 ids, all
boundary; `CISO_NET_IMPORT/EXPORT/NET_ITC` aggregates included), matching the
FNM ITC/BG reference document exactly. The hourly OTC/TTC rating machinery is
real and fetchable — for interties. If CAISO ever re-enforces an internal
path branch group, route 1/3 becomes the intake path with zero new plumbing
(the PJM `transfer-interface-limits` datatype seam is the consumption
pattern); nothing short of that market-design change re-opens this survey.

**What reality does instead (DMM census — the structural finding):** the
S→N congestion our single 5,400 MW link represents binds in reality as
**individual flowgates on the corridor's constituent elements**, dominated by
(2023 annual, ch. 6, with published average binding limits; 2024 annual and
Q3-2025 confirm the same census with binding shares but no MW):

| element (constraint id) | direction | DMM avg binding limit (2023) | binding record |
|---|---|---|---|
| Gates–Midway #1 500 kV (`30055_GATES1_500_30060_MIDWAY_500_BR_1_1`) | S→N | **2,500 MW** | 2023: >80 % of congestion 8a–3p, 90 % Sep–Dec; **2024: bound 9 % of ALL hours**, HE9–15 |
| Moss Landing–Las Aguilas 230 kV (`30750_MOSSLD_230_30797_LASAGUIL_230_BR_1_1`) | S→N | **340 MW** | 2023: >70 % 9a–3p, Apr–Oct; **2024: bound 24 % of hours; Q3-2025: 27 %**, HE9–16 |
| Tesla–Los Banos #1 500 kV (`30040_TESLA_500_30050_LOSBANOS_500_BR_1_1`) | S→N | **1,600 MW** | 2024: bound 6.5 %, HE10–16, winter-heavy |
| Panoche–Gates #2 230 kV (`30790_PANOCHE_230_30900_GATES_230_BR_2_1`) | S→N | **200 MW** | 2023 Q1, 9a–4p |
| Midway–Vincent #2 500 kV (`30060_MIDWAY_500_24156_VINCENT_500_BR_2_3`) | N→S | **≈2,100 MW** | 2023: 50 % of congestion 5–8 pm, >90 % Jun–Aug; prominent again Q3-2025 |
| Path 26 Control Point 1 nomogram (`6410_CP1_NG`) | N→S | **1,600 MW** | "mitigates the Midway–Whirlwind line for the Midway–Vincent #1+#2 contingency"; after 6 pm, Jul–Sep 2023 |

Individual elements bind at 200–2,500 MW while our link waits for the
aggregate to reach 5,400 — this is the measured anatomy of "under-bound and
~30× shallow". But these are element limits under real shift-factor
loadings, seasonal outage states, and contingency dressing: **no formulaic,
residual-blind reduction maps them onto one static link cap** (rule 14's
misalignment clause names exactly this case; the reconciliation this time is
not a number but the §C conclusion that no number exists).

## §C — The bounding what-if (deliverable 2, adapted to the null): exceedance curves and the identifiability kill

Instrument: `scripts/probes/_caiso218_limit_whatif.py` + committed
`results/calibration/_caiso218_limit_whatif.json`. NO LP — the committed
caiso-217 crosswalk-ACTIVE recon (the licensed caiso-105/131 fleet-only
input assembly, caiso-217 cache namespace) rebuilt and **verified to
reproduce the committed caiso-217 stats EXACTLY before any curve is
written** (hours-over-path, belly mean, max, hours-positive — both cuts, all
three years; demand row-match ≤0.5 MW in all 7 zones). For a grid of
hypothetical single-link caps X (dense 250-MW steps plus the DMM element
marks), the curves count recon hours with cut-15/cut-26 surplus > X.

Cut-15 (Path 15 S→N; armed 5,400), hours over X, [2023 / 2024 / 2025], with
reality's committed split-hour vector **[1,310 / 1,691 / 1,347]**:

| X (MW) | mark | hours over X |
|---|---|---|
| 340 | Moss Landing element | 1,454 / 1,800 / 2,212 |
| 1,600 | Tesla–Los Banos element | 967 / 1,378 / 1,882 |
| 2,500 | Gates–Midway #1 element | 682 / 1,124 / 1,601 |
| 3,000 | Path 26 S→N catalog | 523 / 981 / 1,456 |
| 3,265 | Path 15 N→S catalog | 462 / 916 / **1,368** |
| 4,000 | — | 318 / 765 / 1,138 |
| 5,400 | **armed** | **121 / 480 / 742** |

**The identifiability kill.** The recon's exceedance count is strictly
year-ordered 2023 < 2024 < 2025 at EVERY X (the south surplus grows
monotonically, +3.1 → +5.2 GW s-neg mean), while reality's split-hour vector
is NON-monotone (2024 > 2025 ≈ 2023). Consequences, read off the committed
curves:

* X ≈ 3,265 reproduces 2025 almost exactly (1,368 vs 1,347) — and delivers
  only 462/916 in 2023/2024 (needing 1,310/1,691).
* Matching 2023 or 2024 needs X ≈ 400–600 — which overshoots 2025 past
  2,100 h and floods 2023 belly hours reality never splits in.
* **There is NO X — hence no measured static or seasonal-scalar cut limit,
  had one existed — that lands all three years.** The lever class "tighter
  static limit on the single link" is insufficient for the C3a target
  independent of sourcing. What reality's year pattern requires is
  YEAR-VARYING constraint geometry — exactly what the DMM record shows
  (element-level, outage-season-driven binding windows that move: Gates–
  Midway Sep–Dec in 2023 but Q1+April in 2024) — and/or the sub-zonal
  strandedness of caiso-216 §F.3a. The residual attribution tightens onto
  §F.3a/strandedness **with measured weight**, exactly as the charter
  pre-registered for the null.

Cut-26 confirms caiso-216's allocation verdict from the other side: even at
X = 200 MW the south3 surplus exceeds X in only 332/718/1,001 h vs reality's
688/1,230/964 south-negative hours — the model's south3 lacks the surplus
regime at ANY cap in 2023/24; nothing about a Path-26 limit is the binding
issue.

**Fence, restated as a standing kill (§F):** no value from these curves —
and no value backed out of reality's split counts — may ever be armed as a
limit. That is the outcome pin in a limit costume, pre-forbidden by the
charter and now also pointless by the identifiability result.

## §D — Secondary track (deliverable 3): the Kern/Tehachapi collector export instrument — NAMED, half-found

The caiso-216 §F.3a fence required a citable instrument before any gen-pocket
topology is proposed. The survey found the instrument's NAMES but not a
published LIMIT value:

* **`30060_MIDWAY_500_29402_WIRLWIND_500_BR_1_1` (Midway–Whirlwind 500 kV)**
  — the TRTP Tehachapi-collector trunk — appears in DMM's 2023 top-25 CAISO
  15-minute congestion table, and the **`6410_CP*_NG` Path-26 control-point
  nomogram family** manages it (DMM 2023: CP1 "mitigates the
  Midway–Whirlwind line for the contingency of the Midway–Vincent #1 and #2
  lines", avg binding limit 1,600 MW, N→S, evening/summer). CP6/CP10 appear
  in the 2024/2025 censuses.
* Its binding/shadow record is fetchable (route 4) within retention; its
  LIMIT series is not published (same wall as §B route 4).
* No Kramer/Tehachapi/Whirlwind/Windhub element appears in the 2024-annual
  or Q3-2025 top-congestion tables at all — the pocket's export binding is
  episodic, not a standing top-congestion object, consistent with
  caiso-216's Local-class (sub-zonal) curtailment attribution rather than a
  hard standing export cap.
* LCT reports remain import-side only (re-confirmed misalignment).

Verdict: the §F.3a prerequisite is **half-met** — citable constraint
identities exist; a citable export-limit VALUE does not. Any future
gen-pocket proposal must bring its cap from a published static
rating/deliverability record with the rule-14 misalignment documented, or it
is not proposable. Survey only; nothing proposed today.

## §E — The ask (deliverable 4): NOTHING, plus one owner decision item that is NOT this lever's

Phase 0's answer is the decisive null, so per the charter **this lane asks
for no intake and no solve**; NOT-YET stands on the committed caiso-200
keeper (owner ruling 5: C3a must genuinely pass; the honest fallback is
NOT-YET).

One item is surfaced for the owner SEPARATELY from this lever, because §A
found it and nobody else has recorded it: **the caiso-217 crosswalk solve is
complete-but-lost, unregistered, and unrepairable except by re-solve.** The
re-solve at HEAD is exactly a `caiso200_h1_memberpanel` recipe replay (the
crosswalk is data, already active), i.e. the same one-solve ask the owner
already funded once at caiso-216 §G Ask 2 — re-spent. If funded, it re-scores
under the ALREADY-COMMITTED caiso-216 §G gate table with baselines at the
committed values (C3a ×3 with 2023 in band ±10; **C3b MUST-NOT-REGRESS vs
0.098/0.179/0.182**, the committed triplet, NOT the handoff's uncommitted
0.100/0.177/0.180; C8/D unchanged; C6 re-attested; DOF 10/7 + measured rows
only; `_caiso217_zonal_decomp.py` run as the split witness; a 2024-only pass
pre-registered NOT a determination flip), registers under rule 15, and
restores the CAISO bench stamp as a by-product (standing filed item 5). If
not funded, the crosswalk remains committed data whose solve-side effect is
unscored on the record, and the lane stays at rest. Either answer is
consistent with this FINDING; no default is assumed.

## §F — Records, fences added, filed items (rule 28b — CAISO shard only)

Committed by this session (branch `claude/caiso-path-operating-limit-hbe4h0`):

* This FINDING; `scripts/probes/_caiso218_limit_whatif.py`;
  `results/calibration/_caiso218_limit_whatif.json` (controls exact).
* The caiso-217 FINDING §D–§F gap addendum (§A here).
* `docs/calibration-log/caiso.md` caiso-218 entry (also closing the
  caiso-217 numbering; next number caiso-219); matrix §5.2 caiso-218 block;
  CAISO shard `gates` stamp + `measured_interface_limits` evidence append
  (NO verdict moves — nothing was tested).

DO-NOT-REDO additions (append to the caiso-202 §I / 215 §I / 216 §I chain):

1. **Never re-survey the public record for an internal Path-15/26 operating
   limit series** absent a CAISO market-design change re-enforcing internal
   path branch groups (the 2018-11-01 discontinuation is structural; the
   walls in §B are complete: TI-keyed rating/outage machinery is
   boundary-only, constraint reports are shadow-price-only, DMM limits are
   element-grain annual scalars).
2. **Never arm a cut limit chosen from the caiso-218 exceedance curves,
   from reality's split counts, or from any binding-hour record** — the
   outcome pin, now also proven pointless by §C.
3. **The static single-link limit lever CLASS is measured insufficient**
   (the §C identifiability kill): any future limit-side C3a proposal must be
   year-varying and element-grounded (e.g. a published outage-driven derate
   record — which today does not exist publicly for these elements) or
   sub-zonal (§F.3a), never a re-pick of the single-link scalar.

Filed items: the committed census stands at caiso-216's SEVEN (the handoff's
"SIX (caiso-217 FINDING §F)" cites a section that never landed); **add
EIGHT — the caiso-217 registration debt** (§A/§E: complete-but-lost solve;
repair = funded replay; until then the crosswalk's solve-side effect is
unscored and the 2023 checkpoint sidecars are a stranded artifact).
Cross-lane items THREE carried unchanged, plus the caiso-213-routed matrix
anchor item.

Keeper, markers, freeze, DOF ledger, every cell verdict: **UNCHANGED**.

**Next number: caiso-219.**
