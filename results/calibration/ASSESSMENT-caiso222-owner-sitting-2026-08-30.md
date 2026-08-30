# ASSESSMENT — caiso-222: THE POST-CLOSURE OWNER SITTING (caiso-186 pattern) — Q1: the C3a disposition question RE-MEASURED on today's record (the caiso-186 NO is **NOT overturned by the arithmetic** — every axis the owner accepted as decisive in ruling 5 is HEAVIER now: 3 ISOs would flip instead of 1, the flip destination hardened from CALIBRATED-WITH-CAVEATS to full CALIBRATED under v3.3, and the amendment is 3–4 protective-rule motions, not 2 — while the one genuinely NEW fact on the other side is that caiso-221 gives C3a exactly the exhaustion-record shape the v3.0 model-class kind was designed for, which is a values question, not an arithmetic one); Q2: the re-open-route census (publication watch items named and testable; the CEII access classes named with their two structural costs; the sub-zonal program has exactly ONE thin data path that does not reduce to the other two routes). Item 3 ADJUDICATED AND EXECUTED (caiso-205 pair pruned). NO LP, NO SOLVE, NOTHING ARMED, NOTHING REGISTERED — committed bytes + the verdict scorer at HEAD (2026-08-30)

**Charter.** The owner's 2026-08-30 caiso-222 handoff: the post-closure sitting
prep on the caiso-186 pattern — decision-support only; nothing here is a grant,
a re-open, or a recommendation the owner has not asked for. Keeper **UNCHANGED**
at `2026-08-26-caiso-220-c1-crosswalk`; determination **NOT-YET stands**; the
in-model queue is **EMPTY** (caiso-185/200) and the lane is at the caiso-201
rest. `calibration-complete.json` and `holdout-freeze.json` **UNTOUCHED**
(CAISO holds NO marker; the freeze is ACTIVE); **2023–2025 only** — no
out-of-training year was solved, scored, read or registered, and every number
in Q1 is a training-window number. No `ScenarioConfig` field, no data byte, no
matrix cell verdict, no derive.

Instruments (committed; no LP, no network):
`scripts/probes/_caiso222_c3a_disposition.py` →
`results/calibration/_caiso222_c3a_disposition.json` — the six-keeper
(seven-config) scorer re-measurement plus the disposition-variant arithmetic,
computed mechanically from each run's scored table per the aggregation
semantics `scripts/calibration_verdict.py` documents (no scorer constant
modified). The prior sitting's instrument and standard:
`docs/handoffs/caiso-186-owner-sitting-2026-08-09.md` §b; the ruling it
produced: `results/calibration/caiso191-owner-rulings-2026-08-11.md` ruling 5.

---

## §0 — Standing state, verified; one precision correction to the handoff text

Verified on committed bytes at this HEAD (`9405aad` base):

* Keeper `2026-08-26-caiso-220-c1-crosswalk`: **NOT-YET**, basis
  *"undocumented out-of-tolerance (FAIL) criteria: price_mean"* — C3a
  **+4.0 % PASS / +12.5 % / +15.5 %** (model lw 56.31/38.96/39.76 vs RT
  54.17/34.65/34.42), the sole load-bearing FAIL; C1 12/12 free 8/8,
  C2/C3b/C4/C6/C8 PASS, C3c the single ledgered caveat, DOF 11/7;
  grade_summary scored 8 / target 6 / commercial 0 / ledgered 1 / fails 1;
  `audit_keepers --iso CAISO` PASS 0/0. Required falls to the ±10 band
  (caiso-221 `A5`): 2024 **−$0.85**, 2025 **−$1.90** lw; 2023 headroom −$7.56.
* caiso-221 (merged, PR #4316) stands as read: the admissible
  curtailment-quantity class CONSUMED (HSL ratio 1.000–1.003), re-placement
  −$0.02, AS reservation rule-19 barred + 0 static hours, gen-pocket
  load-share-dead (−$0.11/−$0.15/−$0.11 at the whole-ZP26 bound), the surplus
  regime 62 % of the 2025 requirement at perfect conversion (−$1.17 vs
  −$1.90); attribution final at this grain (§E); DO-NOT-REDO §G binding.
* **Precision correction to the handoff's state block** (the substance
  survives; the form matters for Q1): *"ERCOT is now CALIBRATED (C3a −7.3 %
  PASS, ercot-236)"* is the **2023 carve-out config** of what is now a
  **TWO-CONFIG KEEPER** (owner ruling 2026-08-26, `keepers/ERCOT.json`
  `config_partition`): forward keeper `2026-08-25-234-eastex-identity`
  (2024–2025 designated span; its **registered 3-year determination is
  NOT-YET on {C3a-2023 −39.7 %, C3b-2023 NRMSE 0.730}**, published at full
  magnitude; scored on its designated span it reads CALIBRATED — verified
  this session, span-restricted read) + 2023 carve-out
  `2026-08-25-236-swcap-clip-k33` (CALIBRATED, 8/8 target grade, zero
  caveats, C3a −7.3 %). Every training year is covered by exactly one
  designated config. Q1 below carries both facts — the carve-out's pass AND
  the registered record's −39.7 % — because a ledgerability amendment's words
  would reach the registered record.

Also observed, unchanged and not this lane's item: the known cross-lane
bench-staleness condition (parts not stamped by the builder at fingerprint
`dbea7bf45111`) printed its standing warnings on the NEISO/PJM scorer runs —
already adjudicated STAMP-ABSENCE-NOT-DRIFT for CAISO (caiso-210/212/213) and
routed off-lane; no new filed item.

---

# Q1 — THE C3a DISPOSITION QUESTION, re-measured on today's record

The caiso-186 sitting (2026-08-09, §b) answered **NO** to making C3a
ledgerable, and owner ruling 5 (caiso-191) accepted its §b.2 inheritance
arithmetic **as decisive**: *"TWO rubric changes, inherit to ERCOT (−32.4 %)
and MISO (−14.1 %), flip MISO for free."* Both inputs have since changed —
ERCOT's 2023 was resolved structurally, and CAISO's residual is now
exhaustively attributed (caiso-221) rather than merely unexplained. This
section re-runs the §b.2 measurement on today's designated keepers and prices
the disposition honestly against today's rubric (v3.5).

## §1(a) — The re-measured table and the flip arithmetic

`calibration_verdict.py` at HEAD against every designated config, committed
artifacts only (`_caiso222_c3a_disposition.json`; DA diagnostic rows
excluded; all spans 2023–2025):

| ISO | config | determination | C3a 2023 | 2024 | 2025 | other FAILs | C3c |
|---|---|---|---:|---:|---:|---|---|
| **CAISO** | `2026-08-26-caiso-220-c1-crosswalk` | **NOT-YET** | +4.0 | **+12.5** | **+15.5** | — | ledgered CAVEAT |
| **ERCOT** | `2026-08-25-234-eastex-identity` (registered 3-yr) | **NOT-YET** | **−39.7** | −0.2 | −7.9 | **C3b-2023** 0.730 | ledgered CAVEAT ×3 (model-class) |
| ERCOT | — same, designated span 2024–2025 | CALIBRATED | — | −0.2 | −7.9 | — | ledgered CAVEAT ×2 |
| ERCOT | `2026-08-25-236-swcap-clip-k33` (2023 carve-out) | CALIBRATED | −7.3 | — | — | — | PASS (180/181) |
| **MISO** | `2026-08-30-miso-188-rvsscope` | **NOT-YET** | +3.5 | −4.3 | **−12.3** | — | ledgered CAVEAT |
| NEISO | `2026-08-17-neiso-99-joint-p1` | CALIBRATED | +3.1 | +5.7 | +1.7 | — | ledgered CAVEAT (non-downgrading) |
| **NYISO** | `2026-08-25-nyiso-155-hydro-repair` | **NOT-YET** | +6.8 | −1.7 | **−10.8** | **C3c FAIL ×3** (0.10×/0.00×/0.00×, UNLEDGERED) | FAIL |
| PJM | `2026-08-15-pjm-162-inputclock` | CALIBRATED | +6.2 | −0.8 | −7.7 | — | PASS |

Changes vs the caiso-186 table: ERCOT's −32.4 % became a **structurally
repaired** −7.3 % PASS on the carve-out (SWCAP clip + k33 — a real market
rule, not an excuse; the −39.7 % survives only as the forward keeper's
registered 3-year record, whose NOT-YET the partition publishes alongside);
MISO's C3a-2025 improved −14.1 → −12.3 % and is still its sole FAIL;
**NYISO ENTERED the C3a-failing set** (−10.8 % 2025, nyiso-155 promoted
2026-08-25 on structural grounds with gates regressing) and simultaneously
carries an unledgered C3c FAIL ×3. Three ISOs' determinations turn on a live
C3a FAIL today: CAISO, MISO, NYISO.

**What a model-class-style C3a disposition changes, computed mechanically**
(the probe applies the documented aggregation order — explicit ledger → the
existing C3c standing rule → budgets → the v3.3 branch — with the single
hypothetical that a C3a FAIL may reclassify to a ledgered model-class CAVEAT;
variant E = explicit-entry form, any C3a FAIL with an owner-signed entry;
variant S = the C3c standing rule's guards (a)–(d) transposed, LONE C3a only;
each at ledgered budget 1 and 2):

| config | today | E, budget 1 | **E, budget 2** | S, budget 2 |
|---|---|---|---|---|
| CAISO caiso-220 | NOT-YET | NOT-YET (budget) | **CALIBRATED** | **CALIBRATED** |
| ERCOT eastex (3-yr record) | NOT-YET | NOT-YET | NOT-YET (C3b) | NOT-YET |
| MISO miso-188 | NOT-YET | NOT-YET (budget) | **CALIBRATED** | **CALIBRATED** |
| NYISO nyiso-155 | NOT-YET | NOT-YET (budget) | **CALIBRATED** | NOT-YET (not lone) |
| NEISO / PJM / ERCOT span+carve | CALIBRATED | unchanged | unchanged | unchanged |

Four arithmetic facts fall out:

1. **Without the budget raise the amendment flips NOBODY** — every
   C3a-failing ISO already spends the single ledgered slot on C3c (CAISO,
   MISO) or hits the budget through the cascade (NYISO). caiso-186 §b.2
   point 3 reproduces exactly: the second amendment (budget 1 → 2) is the
   effective one, and it doubles the excuse capacity of all six ISOs.
2. **With it, THREE ISOs flip on the day of the amendment — all to full
   CALIBRATED** (v3.3: a ledgered caveat no longer downgrades, and the
   non-downgrade is implemented generically over the ledgered kind, so any
   newly ledgerable criterion inherits it automatically). At caiso-186 the
   projection was ONE flip (MISO), to CALIBRATED-WITH-CAVEATS. The
   certification bought per flip is strictly larger now.
3. **NYISO's flip is a CASCADE that consumes an existing guard.** Its C3c
   fails unledgered today only because the standing rule's guard (a) — lone
   failure only, *"it can never mask a second defect"* — sees C3a also
   failing. Reclassify C3a and C3c becomes the lone FAIL, the standing rule
   fires (C6 passes), and both misses are excused with no NYISO-side act.
   This is the structural point: with TWO ledgerable criteria, guard (a) no
   longer protects against the two-miss shape — a run failing both C3a and
   C3c reads CALIBRATED under the E-form. The S-form (transposing the lone
   guard to C3a) avoids exactly this — CAISO and MISO flip, NYISO does not —
   at the cost of an incoherence the C3c rule never had: two standing rules
   whose lone-guards mutually block on the two-miss shape.
4. **ERCOT never flips** (C3b-2023 fails the registered record
   independently; both designated configs already pass C3a) — but the
   registered −39.7 % is still on the record the amendment's words would
   reach. The caiso-186 magnitude-bar argument therefore survives intact:
   words admitting +15.5 % admit −39.7 % unless a magnitude bar is invented,
   and a bar placed between them is a fitted parameter in the governance
   layer (rule 24 in spirit).

## §1(b) — The rubric-architecture blockers, stated honestly

This is a **protective-rule amendment with full inheritance cost, not a
scoring tweak**. What would actually have to move, measured against
`scripts/calibration_verdict.py` at v3.5:

1. **C3a is LOAD-BEARING** (`CRITERIA["price_mean"] = TIER_LOAD`), and its
   band IS the certification claim — the v3.1 comment names C3a as the
   forcing case: *"a mean-LMP miss beyond ±10 % is a MODEL MISS, and
   ledgering it certified a price level the model does not reproduce."*
   Motion 1: `LEDGERABLE_CRITERIA` widened from `{price_tail}` to include
   `price_mean` (reversing the owner amendment of 2026-08-06, made about
   this criterion at this ISO).
2. **The honest entry kind for C3a is model-class, and the v3.0 guard
   refuses it on a load-bearing criterion** (`_apply_ledger`: a model-class
   entry is admissible ONLY for SUPPORTING-tier criteria, fail-closed). No
   measured-input claim exists for C3a — the actuals are sound; what fails
   is the model class's ability to form sub-zonal prices (caiso-221 §E).
   Motion 2: open the v3.0 supporting-tier-only guard for a load-bearing
   criterion (or re-tier C3a — strictly worse: it would demote the primary
   market signal out of the load-bearing set). *The caiso-186 packet counted
   "TWO rubric changes" without pricing this guard; the count was low.*
3. **The budget**: `MAX_LEDGERED_CAVEATS = 1` is derived from ledgering
   being C3c-alone ("exactly one ledgerable criterion exists … 1 is the true
   ceiling"). Motion 3: 1 → 2 — the motion §1(a).1 shows is the effective
   one, and the one that doubles every ISO's excuse capacity, declared ISOs
   included.
4. **The v3.3 interaction (NEW since caiso-186 — v3.3 landed 2026-08-17,
   eight days after the sitting).** As implemented, a within-budget ledgered
   caveat does not downgrade, generically: amended, CAISO/MISO/NYISO read
   **full CALIBRATED**, with C3a reported on the determination basis but not
   in the label. Keeping the flip at CALIBRATED-WITH-CAVEATS requires a
   fourth motion scoping v3.3's non-downgrade to C3c alone. Either way the
   owner must decide this explicitly; silence buys the stronger claim.

The C3c standing rule's guards (a)–(d) were built to keep exactly this
architecture: (a) lone-failure "can never mask a second defect" — §1(a).3
shows a second ledgerable criterion structurally weakens it; (c)
supporting-tier-only, fail-closed — motion 2 removes the tier wall itself,
not an application of it. And the program's own recent record supplies the
live counter-example to "NOT-YET is a dead end": ERCOT's C3a-2023 went
−32.4 % → −7.3 % PASS through a real structural repair (the SWCAP clip made
the offer cap a market rule; ercot-236) executed **under NOT-YET pressure**,
then an owner config-partition ruling resolved the year honestly without
touching `LEDGERABLE_CRITERIA`, the tier guard, or the budgets (the X-2/two-
config discipline says so explicitly). The rubric held and the model got
better.

**The one genuinely new fact on the other side.** v3.0's model-class kind was
designed for *"an owner-accepted limitation of the model CLASS itself … after
the root-cause program has EXHAUSTED the within-class mechanism space,"* each
entry citing the exhaustion record. At caiso-186 that record did not exist
for C3a (§b.4.3: *"an exhaustion claim made over an unclosed, mis-stated DOF
would not survive review"*). Today it does, in exactly the required shape:
queue empty with every cell adjudicated (caiso-185/200), the DOF ledger
repaired and carried (11/7), the admissible instrument class consumed by
measurement (caiso-221 §B/§D), the regime itself undersized for 2025 at
perfect conversion (C-F), the residual attributed at hour grain (§E), and the
re-open routes named. Whether that record now justifies dismantling the
architecture above is a **values decision the arithmetic cannot make** — the
arithmetic only says what it costs (motions 1–4) and who flips (§1(a)).

## §1(c) — What CAISO's determination reads under each option

1. **Status quo.** `NOT-YET`, basis *"undocumented out-of-tolerance (FAIL)
   criteria: price_mean"*, +12.5/+15.5 % at full magnitude; C3c the single
   ledgered caveat; lane at the caiso-201 rest. Nothing certified that is
   not true; the +15.5 % stays a declared miss.
2. **Amended ledger** (motions 1–3, as v3.3 is implemented): **`CALIBRATED`**
   — grade_summary scored 8 / target 6 / ledgered 2 / fails 0; C3a named on
   the determination basis as a ledgered model-class caveat at full
   magnitude, but absent from the label. A +15.5 % mean-price year certified
   inside a CALIBRATED claim. With the fourth motion (v3.3 scoped to C3c):
   `CALIBRATED-WITH-CAVEATS`. Either way MISO flips the same day and NYISO
   flips under the E-form (§1(a)); the amendment is program-wide by
   construction (rule 24/25 — the scorer is one instrument; an ISO-scoped
   verdict rule would be an off-registry channel in spirit, as v3.3's own
   effect-at-amendment note records).
3. **Accepted permanent NOT-YET with the caiso-221 attribution as the
   record.** The determination text is identical to option 1 — what changes
   is the standing record: caiso-221 §E + this packet designate the C3a
   residual **attributed and closed at this representation grain**, with the
   three §E routes (Q2 below) as the only re-openers. The rest becomes a
   terminal rest with a decision map, rather than an implicit pause. No
   rubric motion, no inheritance, no certification change.

## §1 verdict — per the caiso-186 standard

The charter's standard: *"the caiso-186 NO stands unless this measurement
overturns it."* **The measurement does not overturn it; on the axes ruling 5
accepted as decisive it is heavier in every coordinate**: flips 1 → 3
(destination hardened C-W-C → full CALIBRATED), motions 2 → 3–4, the
magnitude the words would admit unchanged at its worst (−39.7 % on ERCOT's
registered record) while the live failing set widened to include a −10.8 %
near-miss the cascade would excuse together with an unledgered C3c. What HAS
changed in the amendment's favour is not arithmetic: the exhaustion record
v3.0 demands now exists for CAISO's C3a (§1(b) last paragraph). The packet
presents both and stops — per the charter, no recommendation beyond the
arithmetic, and the numbers do not make the amendment side trivial; they make
it strictly more expensive than when the owner last declined it.

---

# Q2 — THE RE-OPEN-ROUTE CENSUS (feasibility + trigger; NOT a survey re-do)

The three caiso-221 §E routes, each stated from the existing record with what
it needs and what would trigger it. The caiso-218 §F / caiso-219 §F fences
bind: the walls themselves are **not re-surveyed** — the watch tests below are
the only sanctioned re-checks, each cheap and specific. All three routes are
owner-gated; none is recommended here.

## (i) A CAISO publication change — the exact watch objects

| # | watch object | what would appear | why it re-opens | the cheap watch test |
|---|---|---|---|---|
| W-1 | **Internal path branch groups re-enforced** (reversal of the 2018-11-01 discontinuation) | `PATH15_BG`/`PATH26_BG` in the OASIS TI universe: the hourly rating stack `TRNS_RATING_OTC/_TTC/_TRM/_CBM/_CONSTRAINT` + `RATING_ATC` (`TRNS_USAGE`/`TRNS_ATC`), and `CURTAILED_OTC_MW` events (`TRNS_OUTAGE`) | caiso-218 §B route 1, verbatim: *"route 1/3 becomes the intake path with zero new plumbing (the PJM `transfer-interface-limits` datatype seam is the consumption pattern); nothing short of that market-design change re-opens this survey."* An HOURLY rating stack is year-varying by construction, so it clears the caiso-218 §C static-class kill | `ti_id=PATH15_BG`/`PATH26_BG` today returns ERR 1000; the July-2024 FNM ITC/BG reference carries no Path 15/26 entry. Either changing is the trigger |
| W-2 | **A limit/flow field in the constraint-report family** (`PRC_NOMOGRAM`/`PRC_CNSTR`/`PRC_RTM_FLOWGATE`) | per-constraint limit MW alongside the shadow prices, for the real corridor elements | the census already carries the element IDENTITIES — Gates–Midway #1 500 kV (`30055_GATES1_500_30060_MIDWAY_500_BR_1_1`), Moss Landing–Las Aguilas 230 kV, Tesla–Los Banos #1 500 kV, Panoche–Gates #2 230 kV, Midway–Vincent #2 500 kV, the `6410_CP*_NG` nomogram family, Midway–Whirlwind 500 kV — with shadow-price records fetchable within the ~39-month retention; only the limit field is missing (live column check + spec v5.1.1, caiso-218 §B route 4) | the report family growing a limit/flow column (spec revision) is the trigger; feeds route (iii)'s grain, not the single cut |
| W-3 | **DMM element limits beyond the 2023-annual scalars** | sub-annual (or per-vintage) element binding-limit MW series | today only the 2023 annual report publishes MW (2,500/340/1,600/200/≈2,100/1,600); 2024-annual and Q3-2025 confirm the census with binding shares but NO MW (caiso-218 §B route 5) | each new DMM annual/quarterly: does it print element limit MW? |

Trigger duty, pre-stated: any W-item landing re-opens as a **data-intake
session first, never a solve** (schema → `write_clean` seam → then a chartered
arm with its own precommit), under the standing fences — no cap backed out of
binding hours or split counts (caiso-218 §F.2), and the static single-link
class stays dead whatever is published (caiso-218 §F.3: any future limit-side
object must be year-varying + element-grounded, or sub-zonal).

## (ii) CEII access — the filing/agreement classes and their two structural costs

**The walled object, precisely** (both survey nulls die on it): internal
element thermal ratings and the FNM shift factors that map elements onto any
reduced link — named in the record as **FERC Form 715** (CEII; caiso-218 §B
route 7), the **CRR Full Network Model** (CRR-participant-restricted;
caiso-218 route 7, caiso-219 route 5), and the branch ratings behind the TPD
tables' "Overload %" (caiso-219 §B route 5, §C).

Access classes (desk research on the access regime — permitted by this
charter; the public-record surveys are NOT re-run):

* **A-1 — FERC CEII request (18 C.F.R. § 388.113).** The individual/
  organizational CEII-requester process: a need-to-know statement plus an
  executed non-disclosure agreement, covering CEII-designated filings — Form
  715 power-flow base cases, ratings and diagrams among them. Recurring
  obligation (NDAs renew; redistribution barred).
* **A-2 — CAISO market-participant channels.** CRR Market Participant
  registration (the CRR FNM release under the tariff's non-disclosure
  regime — the exact instrument caiso-218 named "CRR-participant
  registration, restricted"), or a scheduling-coordinator/stakeholder NDA
  class under the tariff's confidentiality article. Delivers the FNM and
  ratings to a *participant*, never to the public record.
* **A-3 — WECC / RC-West data classes.** The public path catalog is already
  armed; the operational element ratings sit behind reliability-coordination
  confidentiality — a membership/agreement class, not a filing.

Two structural costs, stated honestly because they survive any choice of
class:

1. **CEII/NDA-bound bytes cannot enter this repository.** `data/raw` is a
   committed, provenance-cited public store and the dashboard publishes from
   it; a rating series under NDA would need a private-input channel with a
   redaction/attestation scheme that does not exist today — an off-registry
   input in spirit (rule 24) unless that governance object is built first.
   CEII access is therefore not merely a filing; it is a repo-architecture
   decision.
2. **A rating unlocks nothing at pool grain.** caiso-221 C-E killed the
   gen-pocket use on load-share arithmetic *independent of the wall*
   (≤ −$0.15 at the whole-ZP26 bound), and caiso-218 §C killed the static
   single-link class on identifiability. CEII access is only worth its cost
   **composed with route (iii)** — it buys the limit half of a sub-zonal
   representation, not a lever.

Trigger: an explicit owner decision to execute A-1 or A-2 (a legal/commercial
act with recurring obligations), taken WITH the route-(iii) charter it would
serve. Filed item 9 stands exactly as caiso-221 strengthened it: the wall is
real, AND no longer the only thing between the lane and a 2025 close.

## (iii) The sub-zonal topology program — the honest scoping note

What already exists, committed:

* **Membership**: ATL_PNODE_MAP hub membership (the atlas); the caiso-217
  generator-hub crosswalk (446 plants / 41.1 GW, active data); Attachment B2
  deliverability-constraint boundary diagrams (the DFAX circles); the
  `_caiso219_deliverability_census.json` 93-constraint census with
  on/off-peak flags — the off-peak mass located ZP26-side at Gates–Midway
  (Kern 7/10, Fresno 14/19; Tehachapi 0/3).
* **Sub-zonal load**: OASIS `ATL_LDF` per-pnode load distribution factors —
  the caiso-172 precedent derived the Path-15 PG&E load split from 1,668
  pnodes inside `DLAP_PGAE-APND` (day-weighted, measured, zero free
  parameters); the same object generalizes to any sub-zonal cut within a
  DLAP.
* **What every NEW internal link still needs**: a limit. And the limit class
  is the walled rating object — **with exactly ONE published exception**.

**The charter's question answered plainly: does the program have any data
path that does not reduce to route (i)/(ii)?** Yes — **one, and it is
thin**: the DMM 2023-annual element-grain *average binding limit* scalars
(Gates–Midway #1 2,500 MW; Moss Landing–Las Aguilas 340; Tesla–Los Banos #1
1,600; Panoche–Gates #2 200; Midway–Vincent #2 ≈2,100; Path-26 CP1 nomogram
1,600). Three qualifications, none waivable: (a) **single vintage** — 2023
annual only; the 2024/Q3-2025 reports publish no MW, so 2024/2025 links
would carry 2023 scalars; (b) **top-congestion elements only** — the census
is not a network model, and parallel-path allocation onto reduced links is
the exact rule-14 misalignment caiso-218 §B route 5 documents (there for the
single-cut conversion; at element grain the conversion problem is different
but the shift-factor caveat does not vanish); (c) **admissibility
unadjudicated** — the caiso-218/219 fences wall these scalars as single-cut
intake; their use as sub-zonal link limits would need its own rule-13/14
adjudication and precommit, which this packet deliberately does not perform.
Everything richer than this one path reduces to route (i) (a publication) or
route (ii) (CEII).

**Cost class if ever chartered** (recorded per the fence — a scoping note,
never a charter): a **representation-grain program, not a lever** (caiso-221
§E(iii)) — new zones and links with crosswalk + LDF derivations per
sub-zone, LP growth, every armed CAISO mechanism re-validated at the new
grain, full-span rule-16 re-solves, and the caiso-218 §C design risk carried
openly: reality's binding geometry is year-varying and outage-driven
(Gates–Midway Sep–Dec in 2023 but Q1+April in 2024), so single-vintage
static element limits may reproduce the split no better than the single cut
did — sufficiency untested and untestable without the program itself.

---

## §6 — Filed item 3, adjudicated and EXECUTED: the caiso-205 pair comes off

**Adjudication: PRUNE.** The top-15 rule is not the binding constraint (the
CAISO lane held 4 registered runs); the **standing 2026-08-15 site-retention
directive** is: the backcast pages show the current keeper runs, and any run
prior to the keeper — or rejected/inert after it, offering no new mechanism
for closing the C gates — comes off at the next promotion. The pair
(`2026-08-19-caiso205-ctl-headbase` / `-arm-adaptive`) predates the caiso-220
keeper, is the adjudicated-INERT `ercot_storage_adaptive_expectation` A/B
(cell stays I; *"NOT a keeper candidate — adds no structure on this keeper's
path"*, FINDING-caiso205), and its own filing text (caiso-206 §D item 3 /
caiso-207 §6.3) already said it *"comes off at the next promotion in the
ordinary way. Not an anomaly"* — caiso-220 carried the item instead of
executing it; this session executes it.

**Executed**: `prune_iso_runs.py --iso CAISO --keep
2026-08-17-caiso-200-h1-memberpanel` — registry sidecars, `runs/*.js`
payloads and both bundle dirs (`caiso205_control_A`, `caiso205_adaptive_B`)
removed together (the three-store discipline); **no governance citation
dangles** (the script found none — no `--force-uncite` needed; the matrix
`ev` citation is advisory by design and now annotated in the shard).
**Nothing is retracted and no result is lost**: the pair's determinations and
every measured number stand in `FINDING-caiso205-adaptive-ab-2026-08-19.md`,
`PRECOMMIT-caiso205…`, `results/calibration/caiso205_gates.json` (all
retained), the matrix cell, the log, and git history. `audit_keepers --iso
CAISO` PASS 0/0 after the prune. **Scope note**: `caiso-200` is retained
deliberately — it is the immediate-prior keeper and the caiso-220 keeper's
`--replay-bundle` base (the ERCOT site-retention precedent retains exactly
this comparison role); its retention is not item 3's question and is not
adjudicated here.

## §7 — Record changes and filed items (rule 28b — CAISO shard only)

* This ASSESSMENT; `scripts/probes/_caiso222_c3a_disposition.py`;
  `results/calibration/_caiso222_c3a_disposition.json`.
* The caiso-205 pair prune (§6): 2 registry sidecars + 2 run payloads + 2
  bundle dirs deleted.
* Matrix §5.2: caiso-222 block added above caiso-221's; CAISO shard `gates`
  stamp prepended, `updated` bumped, and one **evidence append** on
  `ercot_storage_adaptive_expectation` (the pair's dashboard registration
  pruned; durable evidence unchanged). **NO cell verdict moves — nothing was
  tested.**
* `docs/calibration-log/caiso.md`: caiso-222 entry.
* **Filed items after this session: 3 DISCHARGED (executed §6); 4 carried**
  (standing duty — promoting sessions re-measure the whole scorecard);
  **9 carried** — and Q2 is now its standing decision map: the watch tests
  (i), the access classes + costs (ii), and the one thin non-reducing path
  (iii). Cross-lane items carried unchanged.

## §8 — DO-NOT-REDO (adds; the caiso-202 §I / 215 §I / 216 §I / 218 §F / 219 §F / 220 §E / 221 §G chain carries whole)

1. **Never re-derive the caiso-222 disposition arithmetic while the keeper
   set and rubric version stand** — `_caiso222_c3a_disposition.json` carries
   every number (all seven configs, all four variants). The probe is the
   sanctioned re-measurement and is re-run ONLY after a keeper promotion or
   a rubric version change (it reads committed bytes in minutes).
2. **The Q2 watch tests are the ONLY sanctioned re-checks of the caiso-218/
   219 walls** — a TI-universe/ERR-1000 check, a constraint-report column
   check, and a DMM-vintage MW check. Anything beyond them is the re-survey
   the standing fences forbid.
3. **Never quote this packet as a recommendation.** It measures; the
   caiso-186 NO stands on its own ruling (caiso-191 ruling 5) unless and
   until the owner rules otherwise, and options (2)/(3) of §1(c) are priced,
   not proposed.

## Closing state

Keeper **`2026-08-26-caiso-220-c1-crosswalk`** UNCHANGED — NOT-YET on C3a
alone (+4.0 PASS / +12.5 / +15.5), C3c the single ledgered caveat, C1 12/12
free 8/8, C2/C3b/C4/C6/C8 PASS, DOF 11/7. In-model queue **EMPTY**; lane at
the **caiso-201 rest**, now with this packet + caiso-221 §E as the standing
owner record to re-open from. Dashboard lane: keeper + caiso-200
(immediate-prior/replay base) — the caiso-205 pair pruned (item 3
DISCHARGED). Filed items open: 4 (standing duty), 9 (CEII wall — Q2 is its
decision map). `calibration-complete.json` (no CAISO marker) and
`holdout-freeze.json` (ACTIVE) untouched; **no out-of-training year touched
or read**. No cell verdict moved; nothing armed; nothing registered; no LP
run. **Both Q1 and Q2 are decidable as written; if the owner rules nothing,
NOT-YET stands and the lane stays at rest. THE OWNER MERGES.**

**Next number: caiso-223.**
