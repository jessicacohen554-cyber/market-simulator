# SOCO Addition Desk — ledger (2026-09)

The live record of the SOCO addition program. **This ledger wins where it and
`docs/multi-iso/soco-addition-plan-2026-09.md` diverge on live state**; the plan owns the charters
(§8) and the decisions (§3), this owns who is running what.

Refresh discipline: one refresh = one §0 entry = one ledger commit = one small PR, off a branch
recreated fresh from `origin/main`.

---

## 0. Live state — newest entry FIRST

### r#4 — 2026-09-13 — NOTHING LANDED, AND THAT IS THE FINDING: FIVE LANES ISSUED, ZERO DISPATCHED (main `33a7c961`)

**Graded: nothing, because nothing exists to grade.** `git log cd09607a..origin/main --grep=SOCO -i`
returns only this desk's own r#3 merge and NWPP commits. No branch matches any SOCO stem
(`git ls-remote --heads origin | grep -i soco` → empty). No PR since **#6103** carries a SOCO lane.
Five lanes stand issued and undispatched: **SOCO-13** and **SOCO-21** since r#2 (~8 h), **SOCO-14**,
**SOCO-15** and **SOCO-22** since r#3 (~2 h).

**THE CONTRAST IS THE EVIDENCE, and it is why this is not a harness problem.** In the same window
the **NWPP** program dispatched and landed **three** lanes — NWPP-10 (#6104), NWPP-11 (#6105),
NWPP-13 (#6106), all merged 15:50–15:51 — and NYISO-231, MISO-256, PJM-H3b, CAISO-281 and SPP-38
all shipped besides. **Dispatch works everywhere except here.** Issuance is this desk's act;
dispatch is not, and the desk has now measured the gap rather than assuming a lane was slow.
Under gate **G15** none is graded LOST.

**Card served and RULED (owner, r#4): "Re-emit all five as one paste-ready block."** All five
re-pinned to `33a7c961` and emitted in dependency order in the sitting report. The desk's own
reading, recorded because it shaped the option set: the five are **file-disjoint** and NWPP just
demonstrated three-way concurrency without collision, so serialising them buys nothing.

**A REGISTRATION PIN THIS PLAN WAS MISSING, FOUND BY ANOTHER PROGRAM.** NWPP-10 flagged
`ISO_TO_BA_CODE` as "the W2 novel change" its plan had missed. **SOCO's §2.3 had missed it too**,
and the desk verified the consequence in the live code rather than taking the report on trust:
`data/zone_assignment.py:69` is a **7-key dict pinned to `SUPPORTED_ISOS`**, and `:1092` indexes it
bare — `df[ba == _ISO_TO_BA_CODE[iso]]` — so a registered SOCO without a key raises **`KeyError`**,
not a fallback. Added to §2.3 as a SOCO-20 checklist row. SOCO's case is trivial (`"SOCO": "SOCO"`,
the BA code and the registry key being the same string); NWPP's is not, and its 17→1 map fails
**silently** at 13 call sites. **The lesson is the transfer, not the fix**: two addition programs
chartered four days apart both missed the same pin, so a §2.3-style atomicity list is only as good
as the last program that stress-tested it.

**Also carried to SOCO-13 in its re-emission: NWPP-13 is its sister lane and it has already run.**
Its WEIM STOP gate read **NO** (on-peak 22.6–37.5 % below Mid-C against a ±10 % bar; daily corr
0.74/0.95/0.67 against ≥0.80), the gate was fixed **ex ante** in a pushed PRECOMMIT before any value
was read, **no bar was moved afterwards**, and the lane landed nothing to `_validation-source`. That
is exactly the discipline SOCO-13's charter demands, now with a worked precedent in the same repo.
SOCO-13's re-emission also carries the anchor candidate **SOCO-12** found after its charter was
written — the SEEM Independent Market Auditor's public monthly price series, 2022-11 → 2026-07.

**Gates at `33a7c961`** — unchanged from r#3; the base-branch debt persists:

| Gate | Exit |
|---|---|
| `audit_keepers.py --check` | **1 — RED** (MISO E13 ×4) |
| `check_registry_payload_parity.py` | **1 — RED** |
| `check_gate_a_provenance.py` | **1 — RED** (MISO + NYISO) |
| `check_mechanism_matrix.py` · `check_bench_freshness.py` · `check_golden_manifest.py` | 0 |
| `ci_refactor_guards.py` | **UNREAD** — `numpy` absent in a `DATA PROFILE: code` container |

**Next act:** sitting #5 — grade whichever of the five land, BY CONTENT. **SOCO-20 is issuable the
moment SOCO-15 lands and G22 is discharged**; nothing else blocks it.

---

### r#3 — 2026-09-13 — ALL THREE W1 LANES LAND AND GRADE PASS · SEVEN CARDS RULED · THE EVIDENCE INVERTED TWO OF THE DESK'S OWN RECOMMENDATIONS (main `c93b0d27`)

**Graded BY CONTENT, not by claim** — each FINDING opened and checked against what its dispatch
said. All three W1 lanes **PASS**, and two of them found things the charter did not anticipate.

| Lane | Verdict | What it actually delivered |
|---|---|---|
| **SOCO-10** audit (PR #6091) | **PASS** | Census **336 plants / 788 gens / 70,667.2 MW** — and it caught that the charter's 335/786/70,665.7 is that figure *minus* the MA row while the charter's own per-state list *includes* it: both right about different sets, one labelled. MA **rejected** (plant 67241, Berkshire MA, NERC **NPCC** — a BA-field mis-entry) under a stated two-key rule; FL **kept** (6 plants, SERC, panhandle). Reconciled to Southern's 10-K on an explicit whole-unit-vs-ownership bridge, the wedge proved exactly on nuclear (10-K 4,786.7 vs EIA-860 8,282.4 MW = Oglethorpe 30 / MEAG 22.7 / Dalton 2.2 %). **Gate G19 CLOSED**: `America/Chicago`, DST-aware, hour-ending, measured over all 26,304 rows. CEMS gap **91.6 %** of fossil MW (SPP's was 44.9 %) |
| **SOCO-11** CEMS + 714 + interchange (PR #6083) | **PASS — including the way it failed** | 8/8 CAMPD files landed, every one re-checked against the charter's named sibling `MS_2024` after the fetcher had used a different one. **The FERC-714 gate FAILED and the lane stopped, rescaling nothing** (rule 13) and deriving no share (rule 23). Interchange confirms the charter to **0.001 TWh** and is the cleanest book in the corpus (zero NaN hours, nine DIBAs, three years) |
| **SOCO-12** documents + gas (PR #6092) | **PASS** | **Gate G12 MET** with a real edition and vintage. **SEEM corrected on three counts** — live **Nov 2022** not Nov 2023; SEEM publishes no price *but its Independent Market Auditor does, monthly, publicly, back to 2022-11*; and a **FERC-accepted settlement (2026-01-05)** will oblige hourly posting. Then it **refused its own find as a benchmark** on four disqualifying grounds and re-cast it as a boundedness anchor — exactly what gate G17 demands |

**THE TWO INVERSIONS, because they are the sitting's real content.**

1. **Card S3's recommendation was conditional and the condition failed.** SOCO-10 predicted the
   three OpCos *structurally* cannot sum to the BA (Georgia Power's winter peak 16,284 MW against
   the BA's 47,368 MW); SOCO-11 measured it — **73.2 %**, short **61.4 / 66.2 / 64.2 TWh** in every
   hour of every year, shape right (r ≈ 0.99) and level short, which is the signature of whole
   planning areas absent rather than a scaling error. **The desk recommended 1 zone. The owner ruled
   3 zones on the six-respondent sum, and that is now the plan of record.** The desk's stated risk —
   an attribution nobody has cited — does not vanish with the ruling, so it is *controlled* rather
   than re-litigated: new gate **G22** makes a cited BA-membership basis a hard precondition on
   SOCO-32, and new lane **SOCO-14** exists to produce it. If SOCO-14 returns a documented NO the
   ruling's premise is gone and S3 goes back to the owner — it is not worked around.

2. **Card S8 was answered and the answer is worse than the card assumed — now card S12.** SOCO-10
   found by *calling the live code* that `cod_ramp.effective_cod` always prefers a plant's
   capacity-weighted mean COD for the ONLINE date; the per-unit preference exists only for
   retirement. `load_cod_map()[649] -> (2005, 5)`, so **Vogtle 3 and 4 are online all 12 months of
   2023**. Phantom **+12.979 TWh** (+24.8 %); a 2023 SOCO backcast would read ≈65.41 TWh of nuclear,
   **above measured 2025's 64.17**, inverting the commissioning step and displacing ~13 TWh of gas.
   Blast radius **SOCO 3,040.3 MW vs next-worst SPP 1,127.4** — 2.7×. Ruled: charter the cross-ISO
   repair **before** SOCO-20, as lane **SOCO-15**, never inside the registration PR.

**Seven cards ruled** (verbatim in §2, appended to plan §3): **S3** 3 zones / six-respondent sum ·
**S4** served interchange · **S5** DOE/LBNL ICE VOLL · **S6** winter 26.0 % scalar · **S7** CAES → gas
CT at the **25 MW rating** (SOCO-10 corrected the charter's 110 MW nameplate — a 77 % derate) ·
**S11** this desk charters SOCO-22 · **S12** (new) charter SOCO-15 before SOCO-20. **S9** stays
deferred behind SOCO-13 as the plan says; **S10** waits for a keeper.

**Issued this sitting: SOCO-14 `[OPUS]`, SOCO-15 `[FABLE]`, SOCO-22 `[FABLE]`** — all three created
by rulings at this sitting, all pinned `c93b0d27`, charters in the sitting report.

**SOCO-13 and SOCO-21 (issued r#2) have NOT landed** — no branch, no PR, no FINDING on origin.
**Not graded LOST** (gate G15): the desk asks dispatch status rather than inferring from absence,
and that question is in this sitting's report.

**Gates at `c93b0d27`** — the base-branch debt recorded at r#2 has **grown**, not cleared:

| Gate | Exit | Note |
|---|---|---|
| `audit_keepers.py --check` | **1 — RED** | was EXIT 0 at `7404ef12` twelve hours ago; the MISO E13 rows landed in between |
| `check_registry_payload_parity.py` | **1 — RED** | R-c, CAISO's |
| `check_gate_a_provenance.py` | **1 — RED** | R-d, MISO **and** NYISO |
| `check_mechanism_matrix.py` | 0 | warnings, other programs' |
| `check_bench_freshness.py` | 0 | |
| `check_golden_manifest.py` | 0 | |
| `ci_refactor_guards.py` | **UNREAD** | `numpy` absent in a `DATA PROFILE: code` container; not carried forward green |

**Next act:** sitting #4 — grade SOCO-13/14/15/21/22 by content, then issue **SOCO-20** (its G12
blocker is now MET; it still needs S3's G22 discharged and SOCO-15 landed first).

---

### r#2 — 2026-09-13 — CARDS S1 AND S2 RULED · SOCO-13 AND SOCO-21 ISSUED · rules 33/34/35 folded into the plan (main `7404ef12`)

**What happened.** Both pending cards were re-served as clickable decision cards and **both were
ruled**, which unblocked two lanes in one sitting. The desk also performed the refresh edit it owns
rather than a lane: CLAUDE.md gained rule **35 `[R-PROMOTE]`** and a **correction to rule 34(a)**
after this program was chartered, and neither was reflected anywhere in the plan.

**Graded — nothing, and deliberately not graded LOST.** SOCO-10/11/12 have no branch, PR or FINDING
on `origin` (`git ls-remote --heads origin | grep -i soco` → empty; `git log origin/main
--grep=SOCO` → only the desk's own two commits). Under handoff §0.3 / gate **G15** branch-name
matching is a weak detector and absence is not evidence, so the desk **asked dispatch status**
instead of grading. The owner confirms **all three are dispatched and running**. They are LIVE at
the r#1 pin `2c2fc065` and will be graded BY CONTENT — the cited FINDING opened, never a green CI
check — at sitting #3. No charter was re-issued.

**Rulings (verbatim in §2 and appended to the plan's §3 rows).**
- **S1 — the key is `SOCO`.** The recommendation as served. `ISO_EV_KEY["SOCO"] = "O"` and the shard
  filename `SOCO.js` follow from it, so SOCO-21's object is now fully determined.
- **S2 — BOTH limbs.** Charter SOCO-13's FERC-EQR index with its pre-registered STOP gate, **and**
  rule the fallback now: with no price benchmark a SOCO run reads a determination naming its own
  basis (e.g. `PHYSICALLY CALIBRATED — price unscored, no public price exists`), scored on
  C1/C2/C4/C6/C8, **never `CALIBRATED`**, price gap on the determination basis at full magnitude.
  Five binding consequences are written into plan §3 so no lane re-derives them. Gate **G17** is
  untouched — a neighbouring hub stays refused, ruling or no ruling.

**Issued this sitting — SOCO-13 `[FABLE]` and SOCO-21 `[OPUS]`**, both verbatim from plan §8 with
§8.0 pasted in and `origin/main` pinned at **`7404ef12`**.
- **SOCO-13** was unblocked by S2 directly; its charter's own first line ("ONLY START AFTER the
  owner has ruled card S2") is now satisfied and the ruling is quoted into the issued prompt.
- **SOCO-21** was unblocked by S1 **plus** a collision-protocol correction (§4 C-2, and §6). Before
  issuing, the desk **measured** that the lane can pass its own gate ahead of SOCO-20: nothing in
  `scripts/lib/mech_matrix.py` or `scripts/check_mechanism_matrix.py` validates `ISO_ORDER` /
  `isos` against `SUPPORTED_ISOS` (`grep` for either returns nothing in both files), and
  `tests/unit/config/test_mechanism_matrix_shard_migration.py:128` documents the precedent in its
  own comment — *"a column is seeded before its first keeper exists (SPP, seeded at SPP-21
  2026-09-06; first keeper at SPP-40)"*. An eight-ISO matrix over a seven-ISO registry is therefore
  a supported intermediate state, not a half-landed matrix.

**Refresh edit — rules 33/34/35 reconciled into the plan.** This is the desk's own work under
handoff §5, not a lane's:
- **G13 REWRITTEN.** As chartered it read *".gitignore the bundle family — never `rm`"*, which
  **collides head-on** with rule 34(a) as corrected 2026-09-12: the SHARD must push its bundle, and
  *"a shard prompt that tells its shard to gitignore or omit the bundle is a defect in the prompt."*
  G13 now states the seam — `.gitignore` is the **parent's** tree; the shard appends a `.gitignore`
  **negation** for its own out-dir and uses a **plain `git add`, never `git add -f`**; the bundle
  must carry `dispatch/<year>_P1.parquet`; the parent keeps per-year dirs out of `main`; never `rm`.
  Left unrepaired, this program's W4 charter would have stranded its first keeper's bytes on an
  ephemeral container — the miso-255 incident, pre-ordered.
- **G20 NEW** (rule 33 `[R-SHARD-ARCHIVE]`): archive on *"the parent has it"*, verify retrievability
  with `git ls-tree` first (34(d)), pin recovery to a **full 40-char SHA**, never delete a branch
  carrying an undecided bundle, and the measured **HTTP 403** on branch deletion with its misleading
  `Everything up-to-date` symptom.
- **G21 NEW** (rule 35 `[R-PROMOTE]`): the promoting session prunes the outgoing keeper's three
  stores; enumerate the year union **before** pruning; the incoming keeper covers it; promote →
  verify (E1) → delete; `audit_keepers.py` **E13** is the invariant.
- **§8.0 collision rules**: rule 7 corrected to the real shard mechanics, **rules 8 and 9 added**
  (archive, promotion). Every future SOCO charter inherits them.
- **SOCO-40's W4 bullet** now carries the mechanics, the S2 price posture, the in-session promotion
  question, and the year-set duty: 2023–2025 IS the union today, but manifest row 9 (holdout
  2019–2022) changes that the moment it lands — thereafter every batch covers the union, one shard
  per year (34(c)), and an unstamped year drops off the report silently (30(a) + 35(c)).
- **Definition of done** row 2 rewritten to S2's ruling; **row 7 added** for the rule-35 invariant.
  **Card S11 added** (§3) — see below.

**Card S11 raised, not assumed.** S2's ruling authorizes the determination class; it does not write
it. `scripts/calibration_verdict.py` carries no branch that can express it, so **W4 cannot score
until someone does**. Plan §1 says this desk does not charter rubric changes — but that prohibition
was written when the question was unruled. The desk **recommends** chartering it itself as
**SOCO-22 `[FABLE]`**, narrowly scoped (an added branch no existing ISO can reach, byte-identity
proof over all seven keepers' verdicts as the exit), because routing it to a desk with no reason to
prioritise it is exactly how R-a sat open. **The desk did not act on its own recommendation** — the
card is served at sitting #3.

**Gates at `7404ef12`** (7 run, exits recorded, none carried forward):

| Gate | Exit | Note |
|---|---|---|
| `audit_keepers.py --check` | **0** | 0 failures, 3 warnings |
| `check_registry_payload_parity.py` | **1 — RED** | 1 failure, **not this program's**: `results/calibration/caiso279_ablate_dswcouple_span` is a dead solve output mapping to no retained sidecar. ROUTED (§3 R-c) |
| `check_gate_a_provenance.py` | **1 — RED** | 1 failure, **not this program's**: NYISO's `gate.a_keeper_marker` cites superseded `2026-09-09-nyiso-221-fuelvintage-span` against live `2026-09-12-nyiso229-hourgrain-span`. ROUTED (§3 R-d) |
| `check_mechanism_matrix.py` | **0** | 3 warnings, all other programs': 2 anchor-line drifts, 1 SPP §5.x prose header not naming its keeper. Diff gate NOT RUN (no `--base`) — a 0 here is not a registration verdict |
| `check_bench_freshness.py` | **0** | 34 parts, 0 stale, 34 carrying engine drift |
| `check_golden_manifest.py` | **0** | 57 manifests / 100 entries; 28 stale vs the live keeper, reported not failed |
| `ci_refactor_guards.py` | **UNREAD** | `ModuleNotFoundError: No module named 'numpy'` — this is a `DATA PROFILE: code` container. Recorded UNREAD, **not** carried forward green (handoff §0.6) |

**The two REDs are the desk's own gates G13 and G21 observed live in other programs**, one day after
the rules that name them landed. That is why the refresh edit was not deferred.

**ADDENDUM (same sitting, after the push). CI on this desk's own three-markdown-file PR came back
with FIVE red checks, and every one is a base-branch condition in another program's files** — which
is the desk's seven-gate read at `7404ef12` reproduced by CI on `c4d4a108` and then some. Verified
by re-running the same checkers in-session against this tree, never by reading the red ticks:

| Failing CI check | What it says | Whose |
|---|---|---|
| Keeper-integrity gates | `audit_keepers` FAIL — **4× E13 on MISO**: `2026-09-09-miso-250-ep-gas` registered but neither keeper nor stamped, and `miso-251-{screen2022,tp2020,tp2021}` each stamped to that superseded id; + E11 (NYISO lineage baseline) and 3× E3 | MISO lane |
| FR-21 forecast-board staleness | gate-(a): MISO **and** NYISO markers both cite superseded keepers | capx gate (a) / promoting lanes |
| Ruff lint + format | 2 errors, e.g. unused `drift` at `scripts/gen_nyiso229_attestation.py:63` | NYISO lane |
| Pinned default cache key | default key `1eefed492204fab7` → `bd2b4657f9b5df7e` — a `ScenarioConfig` field landed without its pin re-mint | capx |
| Structural refactor guards | the same key mismatch, 1 failed / 99 passed | capx |

**Stood down with one PR comment and no ported fix, because every repair lives in `src/`, `scripts/`
or `frontend/data/backcast/`** — surfaces this desk is forbidden to write, and no fix PR exists that
the desk has read. **No re-run spent**: a hash-literal mismatch, a registry identity mismatch and a
static lint error are deterministic, and the confirmation a re-run would give was taken by running
the checkers directly instead.

**The finding that matters more than the standing-down.** The four MISO `E13` rows ARE rule 35
`[R-PROMOTE]` (f)'s invariant firing on a real unswept promotion — the same failure mode this desk
wrote into the plan as gate **G21** hours earlier, before this CI run existed, and while the desk's
own local read at `7404ef12` showed `audit_keepers` at **EXIT 0**. Between that read and CI, MISO
promoted and did not sweep; the count went 0 → 4. **A gate this desk added on principle went red on
`main` the same afternoon, four times over.** Recorded here because the desk's r#2 entry above says
the two REDs were "why the refresh edit was not deferred" — this strengthens that claim rather than
merely repeating it, and it is the second unswept promotion (NYISO) plus a third ISO's, inside one
week of the rule landing.

**Next act:** sitting #3 — grade SOCO-10/11/12 BY CONTENT, grade SOCO-13/21, serve **S3–S9** with
W1's evidence and **S11**, then issue W2 (SOCO-20 — still additionally blocked on manifest row 7,
the LTLF edition + vintage, gate G12).

---

### r#1 — 2026-09-13 — W1 ISSUED (main `2c2fc065`)

**What happened.** The owner directed the desk to issue the first wave. Charters **SOCO-10**,
**SOCO-11** and **SOCO-12** were issued verbatim from plan §8 W1, each with §8.0's collision rules
pasted in and `origin/main` pinned at **`2c2fc065`**. The charter commit `6f2dbe23` is **on main**,
so every lane reads the plan, the handoff and this ledger from `origin/main` — no lane needs a
branch reference.

**SOCO-13 (the FERC-EQR price index) was NOT issued** and is held exactly where plan §5 puts it:
behind owner card **S2**. Issuing it unruled would have a `[FABLE]` lane construct the benchmark
every later price criterion is scored against, before the owner has said whether that benchmark is
wanted or what a SOCO run may be called without one. The desk declines to pre-empt the card.

**Cards S1 and S2 were served to the owner at this sitting** (plan §3; sitting #1 is where they are
due). Status: **PENDING** until ruled — recorded in §2, not assumed here.

**Collision check before issuance** (handoff §0.4). The surfaces the three W1 lanes own were checked
at the pin: `data/raw/campd-unit-level/`, `data/raw/zone-specific-demand/`,
`scripts/data/fetch_campd_unit_level.py`, `scripts/data/fetch_eia930_interchange.py`,
`docs/multi-iso/00-iso-addition-protocol.md` — the most recent commit touching any of them is
`db5f11ea` (PR #6000, PJM-H1), which is well behind the pin and is not a live lane. **No hold.**
The three lanes are file-disjoint from each other by construction (plan §5 FILES YOU OWN), so they
run in parallel.

**Gates:** not re-run — this refresh commits one ledger entry and touches no code, data or registry,
so every gate's input is unchanged since r#0. Recorded UNREAD rather than carried forward green.

**Next act:** sitting #2 — grade SOCO-10/11/12 BY CONTENT (open each FINDING; never grade on
absence or on a green CI check), then serve cards S3–S9 with W1's evidence, then issue W2.

---

### r#0 — 2026-09-12 — CHARTER (main `ab1267e9`)

**What happened.** The owner asked for a plan and prompt pack to add "whatever ISO Hillabee gas
plant in Alabama is in", using the SPP addition workstream as the reference. The chartering session
measured the answer rather than assuming it: Hillabee Energy Center is EIA plant **55411**,
Tallapoosa County AL, 822.8 MW across three CC generators, balancing authority **`SOCO`** (Southern
Company Services, Inc. - Trans), NERC region SERC — **not an RTO/ISO**. The program is therefore the
addition of a **balancing authority** as the eighth registered region.

**Committed at charter:** `docs/multi-iso/soco-addition-plan-2026-09.md`,
`docs/handoffs/soco-desk-handoff-2026-09-12.md`, this ledger. Nothing else. No code, no data, no
registry touched.

**Measured in the charter session** (plan §2 carries all of it with its provenance; do not
re-derive):

| Fact | Value |
|---|---|
| Fleet, BA `SOCO`, EIA-860 operable | 335 plants · 786 generators · **70,665.7 MW** nameplate |
| By state | GA 41,284.4 · AL 24,494.0 · MS 4,577.7 · FL 309.6 · **MA 1.5 (a source defect — SOCO-10 adjudicates)** |
| By technology (top) | CC 20,702.8 · coal 12,234.7 · CT 11,676.8 · nuclear 8,282.4 · solar 5,825.9 · gas ST 3,839.2 · hydro 3,317.6 · PS 1,306.6 · **CAES 110.0** |
| EIA-930 `SOCO hourly.parquet` | 26,304 rows, 2023-01-01 → 2025-12-31 UTC; 8760 / 8784 / **8753** local-date hours |
| Demand | **229.47 / 239.33 / 239.36 TWh** (2023/24/25) |
| Net position | **net EXPORTER, 10.2 / 10.8 / 13.0 TWh/yr** |
| Nuclear energy | 52.4 → 63.0 → 64.2 TWh — the Vogtle 3 (2023-07) and Vogtle 4 (2024-04) commissionings, both mid-window |
| CAMPD CEMS | **AL and GA ABSENT**; MS present 2019–2026 |
| EIA-930 sub-BAs | **SOCO has none** (the product covers CISO/ERCO/ISNE/MISO/NYIS/PJM/PNM/SWPP only) |
| Probes | EPA CAMPD bulk **200** anonymous (187 MB/state-year) · PUDL FERC-714 parquet **206** · `ferc.gov` **403** · FERC EQR viewer **200** · SEEM site **200** · no `EIA_API_KEY` in the container |

**The program's defining problem, stated at charter so it is never discovered late:** Southern
Company publishes **no LMP, no day-ahead clearing price and no hourly index**, and SEEM publishes
matched volumes but **no price**. Three of the rubric's load-bearing criteria (C3a/C3b/C3c) score
against a committed hourly price series. Card **S2** is the only route to resolving that, and it is
due at **sitting #1**.

**Gates run at charter:** none — the charter commit touches no code, no data and no registry, so
every gate's input is unchanged. Recorded UNREAD rather than carried forward green.

**Next act:** sitting #1 — serve cards **S1** (the registry key) and **S2** (the price / rubric
card) to the owner via AskUserQuestion, then issue W1 (SOCO-10/11/12; SOCO-13 only if S2 rules for
option (a)).

---

## 1. Scoreboard

| Lane | Model | Wave | Status | Branch | FINDING |
|---|---|---|---|---|---|
| SOCO-10 audit | OPUS | W1 | **LANDED r#3 — GRADED PASS** | PR #6091 (`a23a4212`, `b4d0dd92`) | `FINDING-soco-10-2026-09-13.md` + `soco-data-audit.md` |
| SOCO-11 CEMS + FERC-714 + interchange | OPUS | W1 | **LANDED r#3 — GRADED PASS**, gate failure included | PR #6083 | `FINDING-soco-11-2026-09-13.md` |
| SOCO-12 documents + gas | OPUS | W1 | **LANDED r#3 — GRADED PASS**; gate G12 MET | PR #6092 (`738fc0ab`, `98c1fd92`) | `FINDING-soco-12-2026-09-13.md` |
| SOCO-13 EQR price index | FABLE | W1 | **ISSUED r#2, RE-EMITTED r#4** — undispatched ~8 h; carries SOCO-12's anchor candidate and NWPP-13's worked precedent | — | — |
| SOCO-14 BA membership | OPUS | W1 | **ISSUED r#3, RE-EMITTED r#4** — undispatched; gate G22 blocks SOCO-32 | — | — |
| SOCO-15 COD seam (cross-ISO) | FABLE | W1.5 | **ISSUED r#3, RE-EMITTED r#4** — undispatched; **blocks SOCO-20** | — | — |
| SOCO-22 rubric class | FABLE | W1.5 | **ISSUED r#3, RE-EMITTED r#4** — undispatched; **W4 cannot score without it** | — | — |
| SOCO-20 registration | FABLE | W2 | **UNBLOCKED ON CARDS AND ON G12** (S3–S8 all ruled r#3; G12 MET by SOCO-12). Now blocked only on **SOCO-15 landing** (card S12) and **G22** (SOCO-14's citation). Issuable at sitting #4 | — | — |
| SOCO-21 matrix shard | OPUS | W2 | **ISSUED r#2, RE-EMITTED r#4** — undispatched ~8 h | — | — |
| SOCO-30/31/32/33/34 | OPUS | W3 | BLOCKED on SOCO-20 | — | — |
| SOCO-40 first solve | FABLE | W4 | BLOCKED on SOCO-30/31/32 **and on card S11** — the scorer cannot express S2's determination class yet | — | — |
| SOCO-22 rubric class | FABLE | W2/W3 | **NOT ISSUED** — card S11 (sitting #3) decides whether this desk charters it or routes it | — | — |
| SOCO-54/55/56/57 levers | — | W5 | pre-declared, not issuable | — | — |
| W6 forecast entry | — | W6 | ROUTED to the capx director (card S10) | — | — |

## 2. Owner rulings — verbatim, numbered

| # | Card | Ruling | Date |
|---|---|---|---|
| O-1 | charter | *"Use the add spp workstream as a reference and develop a plan and prompt pack to do whatever iso Hillabee gas plant in Alabama is in."* | 2026-09-12 |
| S1 | the registry key | **RULED r#2**, verbatim: *"SOCO (Recommended) — The EIA-930/EIA-860 balancing-authority code. Already the on-disk filename convention (`SOCO hourly.parquet`, `SOCO_fueltype.parquet`), so no crosswalk is invented. Lets every doc say 'balancing authority' rather than 'ISO'."* | 2026-09-13 |
| S2 | price benchmark / rubric class | **RULED r#2**, verbatim: *"Both: build the EQR index AND rule the fallback class now (Recommended) — Issue SOCO-13 to build a footprint-hourly volume-weighted price index from FERC EQR transaction data, with a STOP gate registered before any data is read; AND rule now that if it fails, a SOCO run reads a determination that names its own basis (e.g. PHYSICALLY CALIBRATED — price unscored, no public price exists) scored on C1/C2/C4/C6/C8, never CALIBRATED, with the price gap on the determination basis at full magnitude."* Five binding consequences: plan §3 card S2 | 2026-09-13 |
| S3 | topology | **RULED r#3**, verbatim: *"3 zones now on the six-respondent sum"* — **over the desk's own 1-zone recommendation**, with full knowledge of the desk's stated risk. Conditions the desk attached rather than re-litigating: gate **G22** + lane **SOCO-14**, geographic zone names, and the split is never sold as improving accuracy | 2026-09-13 |
| S4 | seams | **RULED r#3**, verbatim: *"Served measured EIA-930 interchange for the first keeper (Recommended)"* — priced neighbours register default-off as lever SOCO-56 | 2026-09-13 |
| S5 | VOLL | **RULED r#3**, verbatim: *"DOE/LBNL ICE calculator, SERC/Southeast mix (Recommended)"* — $2,000 only as a documented fallback; Brattle cited as method, never value | 2026-09-13 |
| S6 | adequacy | **RULED r#3**, verbatim: *"Register winter 26.0% as the scalar, misalignment documented (Recommended)"* — SOCO is winter-peaking in 2 of 3 backcast years; a seasonal registry for all ISOs was offered and declined as an ISO-addition act | 2026-09-13 |
| S7 | the CAES unit | **RULED r#3**, verbatim: *"Map to a gas CT at the 25 MW rating (Recommended)"* — SOCO-10 corrected the charter's 110 MW nameplate to the source's own 25 MW rating, a 77 % derate | 2026-09-13 |
| S8 | mid-window nuclear commissioning | **ANSWERED AND SUPERSEDED BY S12** — the machinery resolves neither the month nor the year for a brownfield addition | 2026-09-13 |
| S9 | `TAIL_THRESHOLD` | **STILL DEFERRED behind SOCO-13**, as the plan says | — |
| S10 | W6 routing | **PENDING** — due when a keeper exists | — |
| S11 | who implements S2's determination class | **RULED r#3**, verbatim: *"This desk charters it as SOCO-22 [FABLE] (Recommended)"* — one added branch keyed on the ABSENCE of an `actual_lmp.json` block, byte-identity proof over all seven keepers as its exit, serving NWPP's card N2 with the same amendment. Issued r#3 | 2026-09-13 |
| S12 | the COD-seam defect (SOCO-10's R-4) | **RAISED AND RULED r#3**, verbatim: *"Charter a cross-ISO repair lane BEFORE SOCO-20 (Recommended)"* — issued as SOCO-15 `[FABLE]`. Floor stands regardless of outcome: the bias is stated on SOCO's first keeper's determination basis | 2026-09-13 |

## 3. Routed — open, not this desk's to fix

| # | Item | Owner | Why it stays visible |
|---|---|---|---|
| R-a | The rubric cannot express a determination for a region with no price benchmark | **CLOSED r#3** — S2 authorized the class, S11 assigned the scorer, and lane **SOCO-22** is issued | Closed as a routed item; it is now a lane to grade, not an open question. W4 still cannot score until SOCO-22 lands |
| R-b | The NWPP program shares card S2's problem in a milder form. **It is no longer hypothetical: NWPP was chartered 2026-09-13** (`docs/multi-iso/nwpp-addition-plan-2026-09.md`, landed on `main` between this desk's push and its rebase), it cites the SOCO charter as its non-market precedent, and its §2.6 raises card **N2** — the same question | the owner; the NWPP desk | **S2's ruling is the "once", on the CLASS.** The two programs are not identical: NWPP's §2.6 records that WEIM 15-minute LMPs for its BAs are anonymously fetchable (CAISO OASIS `PRC_RTPD_LMP` probed 200), so NWPP may need the no-price class only partially or not at all. What must not happen is **two scorer amendments**: card **S11** should be scoped to a determination class **keyed on the absence of an `actual_lmp.json` block**, which serves any region without a price benchmark, rather than a SOCO-specific branch. This desk surfaces that and does not charter across the boundary |
| R-c | `check_registry_payload_parity` **RED** at `7404ef12`: `results/calibration/caiso279_ablate_dswcouple_span` is a dead solve output mapping to no retained sidecar (Class-E point 4) | the CAISO calibration lane / caiso-279 | Not this desk's file and not this desk's to fix. It is **gate G13 observed live** — the exact failure mode this desk just wrote into its own W4 charter |
| R-d | `check_gate_a_provenance` **RED**, and it grew inside this sitting: NYISO's marker cites superseded `2026-09-09-nyiso-221-fuelvintage-span` (live `2026-09-12-nyiso229-hourgrain-span`) **and, as of `c4d4a108`, MISO's cites superseded `2026-09-09-miso-250-ep-gas`** (live `2026-09-12-miso-255-sil-measured`) | the NYISO and MISO lanes / the capx director's gate (a) | Not this desk's files. **Gate G21 / rule 35 `[R-PROMOTE]` observed live, twice, within days of the rule landing** |
| R-f | **`cod_ramp.effective_cod` prefers a plant's mean COD for the ONLINE date** — a general defect in shared `src/`, worst in SOCO (3,040.3 MW, 2.7× the next footprint) but live in all eight | **NO LONGER ROUTED — the owner ruled it (card S12) and the desk chartered SOCO-15** | Kept visible because the repair moves **results** for all seven registered keepers; each ISO's lane will see its own numbers move and must not read it as its own regression |
| R-g | **SHA256SUMS.txt scope** — SOCO-11 deliberately did not add rows for the tracked 2019-2026 CEMS files, since that file's own header scopes it to the 35 gitignored `<ST>_2018` extracts and git's blob hashes are the tracked files' integrity record | the desk | The desk **agrees with the lane** and records it as correct, not outstanding: adding rows would misrepresent the file's stated scope. No action; noted so a later lane does not "fix" it |
| R-h | **EIA-930 defect screens catch none of the three real SOCO defects** SOCO-10 found (four `NG: NG` hours at ~70 GW against a 36,336 MW gas fleet; the netgen identity breaking in 2025 only, 595 h; a 1-h partial demand dropout) — `_screen_demand_spikes` is high-side only, `_screen_demand_dropouts` is exact-0.0 only, and **no repo screen touches a fuel column at all** | the data/curation owner | SOCO-10 correctly proposed **no new constant** (rule 23 — setting a threshold after seeing the outliers is a fitted threshold). Cross-ISO, not SOCO's to fix |
| R-i | **SOCO's 1,306.6 MW of pumped storage is UNOBSERVABLE in EIA-930 for 2023 and most of 2024** — `NG: PS`/`BAT`/`SNB`/`OES` are a taxonomy cut-over at 2024-07-15, and `NG: WAT` never goes negative before it (min +32 MW), so PS charging was not folded into hydro, it was not reported | SOCO-31 (benchmarks) | A hard constraint on the **C1 `fuelmix`** benchmark, not a bug to fix. Must be stated on SOCO's first keeper's determination basis |
| R-e | `audit_keepers` **E13 RED ×4 on MISO** at `c4d4a108` — `2026-09-09-miso-250-ep-gas` registered but neither keeper nor stamped, and three `miso-251` runs stamped to it; plus E11 on NYISO's missing lineage baseline. Separately: **Ruff** 2 errors (`scripts/gen_nyiso229_attestation.py:63`) and the **default cache-key pin** off its literal (`1eefed49…` → `bd2b4657…`), which reds both the pin check and the structural guards | MISO lane · NYISO lane · capx (cache fingerprint) | All in `src/`/`scripts/`/`frontend/`, none this desk's to write. Stood down on PR #6090 with one comment and no ported fix; no re-run spent (deterministic, reproduced locally). **They will red every SOCO PR until repaired**, so a future sitting must not read them as its own regression |

## 4. Collision register

| # | Surface | Other writer | Action |
|---|---|---|---|
| C-1 | `config/capacity_market.py`, `config/constants.py`, `model/interchange/spec.py` | capx D-lanes, the SCN desk, the per-ISO calibration lanes | SOCO-20 rebases last and appends; the desk re-checks their ledgers' top entries at issuance |
| C-2 | `docs/codebase-site/data/mechanism-matrix.js` (base file) | every ISO's lanes, whenever a field is added | **HOLD LIFTED r#2, and the test itself was wrong.** "Verify nobody is mid-edit" is unsatisfiable: writers on the matrix files are continuous (last base write `26737620` nyiso-230; last shard write `e24c0d90` caiso-279 — both within the pin window). The SPP desk retired the same precondition at its own r#2; the protocol is **rebase immediately before commit, one commit, re-run `check_mechanism_matrix`**, which is what SOCO-21's charter already says. See §6 |
| C-5 | `scripts/calibration_verdict.py` (SOCO-22) and the `cod_ramp` online-date seam (SOCO-15) — both are **shared `src/`/`scripts/` surfaces every ISO reads** | the capx D-lanes, the audit Y-lanes, every per-ISO calibration lane | **Both charters carry a byte-identity exit** (seven keepers' verdicts for SOCO-22; seven keepers' cache **keys** for SOCO-15, whose **results** deliberately move). Each rebases last and re-runs the gates. **SOCO-15 must land before SOCO-20**, so they are sequenced, not parallel |
| C-6 | `data/raw/zone-specific-demand/SOCO/SOURCES.md` | SOCO-11 (landed), SOCO-14 (issued) | **Append-only** for SOCO-14 — it adds BA-membership citations beneath SOCO-11's committed eight-respondent table and edits none of it |
| C-4 | `scripts/lib/mech_matrix.py` `ISO_ORDER`/`ISO_EV_KEY`, `tests/unit/config/test_mechanism_matrix_shard_migration.py` | SOCO-21 (this program), any ISO addition | **Measured gate-independent from SOCO-20 at r#2**: neither `mech_matrix.py` nor `check_mechanism_matrix.py` references `SUPPORTED_ISOS` or `_ISO_BUILDERS`, and the shard test's own comment records SPP's column being seeded before SPP's first keeper. An 8-ISO matrix over a 7-ISO registry is a supported intermediate state |
| C-3 | W1 lane surfaces (`campd-unit-level/`, `zone-specific-demand/`, the two fetch scripts, doc 00) | — | **CHECKED CLEAR at r#1**, pin `2c2fc065`: last touch `db5f11ea` (PR #6000), not a live lane. No hold |

## 5. Issuance record

| Sitting | Date | Lanes issued | Cards served |
|---|---|---|---|
| r#0 | 2026-09-12 | none (charter commit) | none |
| r#1 | 2026-09-13 | **SOCO-10, SOCO-11, SOCO-12** (plan §8 W1, verbatim, pinned `2c2fc065`). SOCO-13 HELD on card S2 | **S1, S2** |
| r#2 | 2026-09-13 | **SOCO-13** (plan §8 W1, verbatim, pinned `7404ef12` — S2 ruled) · **SOCO-21** (plan §8 W2, verbatim, pinned `7404ef12` — S1 ruled, C-2 lifted) | **S1 RULED, S2 RULED**; **S11 raised**, due sitting #3 |
| r#4 | 2026-09-13 | **RE-EMITTED all five undispatched lanes** — SOCO-13, SOCO-14, SOCO-15, SOCO-21, SOCO-22 — as one paste-ready block pinned `33a7c961`, in dependency order (owner ruling r#4). No new lane created | dispatch card SERVED and RULED |
| r#3 | 2026-09-13 | **SOCO-14** `[OPUS]` · **SOCO-15** `[FABLE]` · **SOCO-22** `[FABLE]` — all three created by this sitting's rulings, pinned `c93b0d27`. None existed in the charter's prompt pack, so all three are written charters rather than verbatim copies (plan §5 rows added) | **S3, S4, S5, S6, S7, S11 RULED; S12 raised AND ruled**; S8 answered/superseded; S9 still deferred |

## 6. Errors against interest

*(The desk records its own mistakes here, in its own words, so the next refresh does not repeat
them.)*

**E-4 (r#3, against the charter — the biggest of the four so far). The desk built a plan around a
load spine it never checked, and a two-number test would have falsified it in the chartering
session.** Plan §2.5 declares FERC Form 714 "the zonal-load spine", names **three** respondents, and
card S3 recommends three zones on it. SOCO-10 found PUDL carries **eight** Southern-area respondents,
and disproved the three-respondent premise with arithmetic the charter had every input for:
**Georgia Power's own winter peak is 16,284 MW against a BA winter peak of 47,368 MW**. SOCO-11 then
spent a lane measuring what that implies — 73.2 %, short a quarter in every hour of every year. The
charter did measure a great deal (§2 is dense with real numbers) but it measured the *fleet* side
thoroughly and asserted the *load* side, and the load side was the half card S3 turned on. **A plan
that names a data source as a spine owes that source the same census it gives the fleet** — how many
respondents, covering what, summing to what. Adopted forward: before any future card recommends a
topology, the desk states the load decomposition's **coverage fraction** as a measured number or
says it is unmeasured.

**E-5 (r#3, against the charter). Four numbers the desk asserted that lanes had to correct — three
of them in §2.6, the section the desk called the program's defining problem.** The CAES unit was
carried at its **110 MW nameplate** when the source itself states a **25 MW** rating (a 77 % derate,
so card S7 was written about a unit 4.4× its real size); SEEM was dated **November 2023** when it
launched **November 2022**; SEEM was said to publish **no price** when its Independent Market Auditor
publishes a monthly price series publicly, back to 2022-11, no login; and the census headline
335/786/70,665.7 was the MA-excluded figure sitting beside a per-state list that includes it, with
neither labelled. None changed a ruling — S7 got smaller, S2 got *corroborated* by SEEM's own FAQ
routing price to FERC reporting — but all four were checkable at charter, and the SEEM ones sat in
the paragraph the whole program is organised around. **The desk's own §2 discipline ("no number here
is recalled or inferred") was applied unevenly**: it held for the fleet and the 930 extract and
lapsed for the documents. Adopted forward: a charter's narrative sections carry the same
cite-or-say-pending rule as its tables.

**E-1 (r#2, against r#1 and against the charter). The desk carried a blocking precondition that
cannot be satisfied, and the reference workstream had already retired it.** C-2 said SOCO-21 would
be "issued only after the desk verifies nobody else is mid-edit on the matrix base file." There is
no way to verify that: the matrix base and shards are written several times a day by every ISO's
lanes, and the SPP desk lifted the identical hold at its own r#2 with the finding *"writers on the
matrix files are continuous, so the charter's rebase-immediately-before-commit line is the
protocol."* That lift is in `docs/handoffs/spp-desk-ledger-2026-09.md` §4, which handoff §0.1
instructs this desk to read — so the error is not that the precedent was unavailable, it is that
the desk wrote a precondition without asking whether anything could ever discharge it. **A hold
whose release condition can never be observed is not caution, it is an indefinite block.** Adopted
forward: every hold this desk records names the **observation that releases it**, and if that
observation cannot be made, the hold is a protocol instead.

**E-2 (r#2, against r#1). The r#1 scoreboard understated SOCO-21's block, and the understatement
pointed the wrong way.** The row read "BLOCKED on collision check" alone, while handoff §1 correctly
listed SOCO-21 as blocked on card **S1** as well. The lane's entire object — the shard filename
`SOCO.js`, `ISO_EV_KEY["SOCO"] = "O"`, the `--iso-soco` colour token — is the registry key that S1
decides, so S1 was always the binding constraint and the collision check was the softer one. Had
the desk acted on its own scoreboard it would have issued a lane whose deliverable had no name.
The handoff was right and the ledger was wrong, which inverts the documented precedence (*"the
ledger wins on live state"*) — **the ledger wins on live state, not on dependency structure, and
this desk should re-derive a block from the plan rather than copy it forward from its own last
entry.**

**E-3 (r#2, against the charter). The plan's own G13 would have produced the miso-255 incident.**
As chartered, G13 told W4 to "`.gitignore` the bundle family" — written on 2026-09-12, the same day
rule 34(a) was corrected to say the opposite for a shard, and that a charter saying so is *"a defect
in the prompt."* The charter is this desk's document; the defect was this desk's. It is repaired at
r#2, before any SOCO solve exists, which is the only reason it cost nothing. **Adopted forward: a
CLAUDE.md rule that lands after a plan is chartered is a refresh edit due at the NEXT sitting, not
whenever a lane trips over it.**
