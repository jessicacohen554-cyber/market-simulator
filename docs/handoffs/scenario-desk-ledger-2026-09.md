# Scenario Readiness Desk — Ledger

Standing coordination ledger for the SCN track, implementing
`docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` ("the plan"). Maintained by the
desk session; one refresh = one commit = one small PR. The desk charters lanes and tracks
state — it never solves, never edits `src/market_sim/` or `scripts/`, and never charters
backcast-calibration work or anything on the capacity-expansion director's queue
(`docs/handoffs/capx-director-ledger-2026-08.md`), which it deconflicts with at every refresh.

**Charter date:** 2026-09-05 · **Last refresh:** 2026-09-06 (refresh #4) ·
**r#4 (HEAD `21deb4a7`):** **NOTHING NEW IS UNBLOCKED BY CODE — and the one real unblock this
refresh is GOVERNANCE, is not this desk's to take, and nobody has taken it.** NYISO promoted
`2026-09-06-nyiso-196-extract-basis` — **CALIBRATED, grade 7, zero fails, C3c the lone ledgered
caveat** — and the withdrawal block's own re-entry clause reads *"re-entry is a NEW explicit
owner declaration on a keeper scoring CALIBRATED."* **That condition is now MET and the marker
has NOT been re-declared**: `complete` still reads {ERCOT, NEISO, PJM}, so NYISO's §2.1b leg (a)
is still FAIL and Q45's lapsed premise is still lapsed — **on a technicality that a single owner
declaration clears.** Disclosed and routed to the capx director per charter §0.4; this desk
declares no marker · **SCN-WS4b and SCN-MX-R are LOST** — issued r#2, re-emitted r#3, still no
branch and no PR at r#4, which is the charter's two-refresh threshold → **relaunched verbatim
under `-r2` stems, recorded never-launched against interest, NOT graded as running** ·
**SCN-WS2a's PRECOMMIT and docs legs merged** (#4892) but the probe, the FINDING and the CES
matrix row are still owed — the lane has PRs so it is not lost, it is owed · SCN-WS1b and
SCN-WS2b launched by the owner; no branches yet, which is expected within a refresh · the desk's
own r#3 PR merged (#4888), so the ledger conflict is closed · §2.1b gate unchanged **today**:
**NEISO only** — and NYISO is one declaration away from being the second.
*(previous)* **r#3 (HEAD `ea273339`):** **BOTH r#2 FINDINGS WERE SELF-CORRECTED BY THE LANES THEMSELVES,
BEFORE ANY r#2 PROMPT WAS DISPATCHED** — SCN-WS0 landed items 5 and 6 plus the G-E4 rider
(`e8c7072d`, `79034547`, `47ba0610`) and SCN-WS1a minted the `carbon_price_path` +
`policy_bundle` rows with a cell in every shard (`717de664`) and scored its CAISO T0
(`a147362b`). **THREE OF THE FOUR r#2 CHARTERS ARE THEREFORE WITHDRAWN UNDISPATCHED**:
SCN-WS0-R (its whole scope landed), SCN-WS2a-R (**SCN-WS2a IS LIVE** — two unmerged commits
on its branch, the docs leg and a pushed PRECOMMIT, so dispatching -R would build a twin),
and SCN-MX-R's carbon half. **SCN-MX-R survives NARROWED** to the one thing still unowned:
why `check_mechanism_matrix.py` exited 0 on a PR that added two `ScenarioConfig` fields with
no row · **the desk's r#2 PR conflicted on the ledger and is resolved here by rebuild** —
this refresh is r#2's record plus r#3's, on top of `ea273339`, with SCN-WS0's own §3 edits
taken over the desk's (better sourced) · **WS-0's T0 returns the campaign's first substantive
result and it is a CARBON-LEAKAGE number**: $25/t cuts NEISO's modeled in-ISO CO2 −2.71 Mt
(−16.6 %) while the reported import line rises **+1.85 Mt on a single NYISO rung**, so
**about two thirds of the headline reduction leaves the scored basis** — and at a CT-realistic
0.53 t/MWh instead of the 0.428 disclosure default the net shrinks to ≈ −0.42 Mt. Every
campaign delta must now be read with the import line beside it, per ISO · **ISSUED: SCN-WS1b
and SCN-WS2b (both newly UNBLOCKED by WS-0 item 5), SCN-MX-R (narrowed); SCN-WS4b RE-EMITTED
verbatim** (issued r#2, no branch at r#3 — one refresh, so NOT graded lost; dispatch status
asked) · no card ruled: **D-1, D-2, D-3, D-4, D-6 and the new sub-boxes all still OPEN** ·
§2.1b gate unchanged, **NEISO only**; no Stage-B lane issuable, none issued.
*(previous)* **r#2 (HEAD `db8b6015`):** **ALL FIVE WAVE-1 LANES LAUNCHED AND LANDED WORK — three complete, two
CHECKPOINTS.** WS-1a delivered items 2–4 + the Phase-0 table + the D-1 memo and **STOPPED on its
card gate exactly as chartered** — and its Phase 0 **proves G-C1 with a number**: `policy_bundle
="tight"` is a carbon-price CUT of **$16–$102/t in every one of 25 years** on CAISO/NYISO/NEISO,
and under the recommended FLOOR the RFF mid path **never once exceeds** a program trajectory, so
the floor makes `tight` an exact **no-op** there rather than a fix — a new D-1 sub-question, not a
new answer · WS-4a **complete**: ERCOT was already fully populated (the plan's "only for PJM" line
was stale), MISO populated from the 2026 LTLF regional decomposition validated on the deck's own
published totals, NEISO `{}` re-confirmed, D-4 gap list presentable unedited · WS-3a **complete**
(and **launched twice** — two branches ran the same charter; the second merged as a cross-check
addendum, no divergence) · **WS-0 CHECKPOINT** (items 1–4 + PRECOMMIT landed; the `scenario`
registration kind and the paired T0 owed) · **WS-2a CHECKPOINT** (the row + two fields landed;
postures/probe/matrix/docs owed) · **GRADED AGAINST CLAIM, TWICE: no matrix row or cell exists for
`carbon_price_path`, `policy_bundle`, or `federal_ces_target_by_year`** — WS-1a's own scorecard
edit reads "stamped … minted at WS-1a" and it never committed to `docs/codebase-site/data/` at
all; WS-2a added two solve-affecting `ScenarioConfig` fields with no row, **and CI passed**, so
`check_mechanism_matrix.py`'s duty-(c) half did not catch them (routed, not fixed) · **ISSUED:
SCN-WS0-R, SCN-WS2a-R, SCN-MX-R, SCN-WS4b** · **cards D-1 and D-3 RE-PRESENTED on new evidence,
D-4 PRESENTED** (its gap list now exists); D-2 and D-6 stand presented, unmoved · no card has been
ruled — **D-1, D-2, D-3, D-6 all still OPEN** · §2.1b gate unchanged: **NEISO only**; no Stage-B
lane issuable, none issued · capx r#41 deconflicted: D62/D65 issued, D60-R2 status ASKED not
graded lost, none holds an SCN file.
*(previous)* **r#1 (HEAD `d01ab8b0`):** the desk opens. Ledger created; plan read whole; capx r#40 read for
deconfliction (**D60-R2 RUNNING**, D61/D64 issued-unlaunched, D58 released-pending-D60, D63
queued — none holds a wave-1 SCN file, but D60-R2 and the owner's backcast lanes append to the
six matrix shards continuously, so the last-commit one-line shard protocol is MANDATORY, not
advisory) · **WAVE 1 ISSUED IN FULL — SCN-WS0, WS-1a, WS-2a, WS-3a, WS-4a** (five disjoint-file
lanes, no owner ruling required to start any of them) · **cards D-1, D-2, D-3, D-6 PRESENTED**;
D-4 held for WS-4a's gap list, D-5 held for Stage A's measured cost table · **§2.1b gate read at
the pin: NEISO ONLY** — NYISO's `complete` was withdrawn again on 2026-09-05 (nyiso-193
executing the owner's nyiso-192 promotion ruling; Q5 uniform rule), so `complete` =
{ERCOT, NEISO, PJM} and Q45's premise has lapsed. No Stage-B lane is issuable at this refresh
and none is issued.

**Transport note (r#1):** this session's harness assigns the branch
`claude/scn-desk-charter-x9v4k4` and forbids pushing elsewhere, so this refresh lands there
rather than on the charter's nominal `claude/scn-desk-ledger`. Successor refreshes should use
`claude/scn-desk-ledger` unless their own harness says otherwise; the ledger file path is
unchanged and is what matters.

---

## 0. Refresh log (newest first)

### r#4 — 2026-09-06, main HEAD `21deb4a75fd2d2c1d1b2c8ed4070968fe818313c`

*(PR #4894.)* Delta from the r#3 pin `ea273339`: **14 commits** — the desk's own r#3 (#4888,
merged), SCN-WS2a's two branch commits (#4892), wallclock A-2/A-6, and nyiso-196.

**THE ANSWER TO "WHAT ELSE IS UNBLOCKED": nothing, by code.** Checked against every queued
lane's actual precondition, not its label:

| lane | precondition | state at `21deb4a7` |
|---|---|---|
| **SCN-WS4c** | WS-0 ✓, WS-4a ✓, **WS-4b** | still blocked — WS-4b is LOST, relaunched here |
| **SCN-WS3b** | D-3 ruled + WS-3a boxes + WS-2a ✓ + WS-4a ✓ | blocked on **the card alone**; both code preconditions met since r#3 |
| **SCN-WS5A** ×6 | the whole wave-2 set | blocked — WS-1b/WS-2b in flight, WS-2a owed, WS-4b/c not started |
| **Stage B** | card D-5 **and** an open §2.1b gate | not issuable; D-5 is held until Stage A's measured cost table exists, which is the correct order |

**THE ONE REAL UNBLOCK IS GOVERNANCE, AND IT IS NOT THIS DESK'S TO TAKE.** On 2026-09-06 the
owner-track lane nyiso-196 promoted `2026-09-06-nyiso-196-extract-basis` and it reads
**CALIBRATED — grade 7, fails 0, C3c the lone ledgered caveat**, on a rule 14 + rule 13 + rule 1
basis with zero free parameters and zero new DOF entries. NYISO's `withdrawn` block states its
own re-entry condition verbatim: *"re-entry is a NEW explicit owner declaration on a keeper
scoring CALIBRATED."* **The condition is satisfied. The declaration has not been made** —
`calibration-complete.json` `complete` still reads {ERCOT, NEISO, PJM} at this pin. Consequences,
stated because they are this desk's to track even though the act is not:
- FF §2.1b leg (a) for NYISO stays **FAIL** while the marker is absent, so no NYISO forecast
  campaign is authorizable, and **Q45's premise stays lapsed** — the capx director recorded at
  r#40 that no re-authorization card is served until a CALIBRATED NYISO keeper returns. **It has
  returned.**
- If and when the owner re-declares, NYISO becomes the **second** ISO whose Stage-B campaign is
  askable, behind NEISO — which changes what card D-5 should ask for when Stage A lands.
- **This desk declares nothing.** Markers, keepers and defaults are the owner's, and the backcast
  records lane is the capx director's queue (charter §0.4: disclose per case, never fix).
  **Routed to the capx director**; surfaced to the owner in this refresh's report. Recorded here
  so that if the marker is *deliberately* being withheld, the reason is asked for rather than
  assumed.

**LOST — two lanes, and the charter's own threshold decides it, not judgement.** SCN-WS4b and
SCN-MX-R were issued at r#2 and re-emitted/narrowed at r#3. At r#4 `git ls-remote origin
'refs/heads/claude/scn-*'` returns **nothing** for either, and no PR exists. That is **two
refreshes after issuance**, which is the charter's LOST threshold. Applying the relaunch protocol
exactly as written: **re-issued verbatim under fresh `-r2` stems, recorded "never launched"
against interest, and NOT re-graded as running.** The r#2/r#3 stems are burned. This is the
second time the desk has had to note the same asymmetry: the five r#1 lanes all launched within
hours, so a lane that shows no branch across two refreshes was almost certainly never dispatched
rather than silently failing.

**RE-GRADED — SCN-WS2a, the one lane still mid-charter.** Its two branch commits merged at #4892:
`73e5351f` (the `05-policy.md` + G-S6 docstring legs, item 6's doc half) and `6e6449ab` (the
NEISO T0 PRECOMMIT, `PRECOMMIT-scn-ws2a-2026-09-05.md`, pushed before the solve as rule 29
requires). **Still owed: the probe result, the postures tests, the FINDING, and the CES matrix
row** — `federal_ces_target_by_year` remains absent from `mechanism-matrix.js` at this pin
(verified: 0 occurrences), so the rule 28 duty-(c) gap SCN-MX-R was chartered to diagnose is now
confirmed across **three** pins. The lane holds merged PRs, so it is **owed, not lost**; the
relaunch protocol does not apply to it and SCN-WS2a-R stays withdrawn.

**Launched by the owner, not yet visible:** SCN-WS1b and SCN-WS2b. No branches at this pin, which
is normal inside one refresh — both were dispatched after r#3. They are graded RUNNING on the
owner's statement, and will be graded by content at r#5.

**Capx deconfliction.** No new capx lane since r#3; D65's branch is still live (`43b3a737`) and
touches no SCN region. The matrix tree has three pending SCN writers (WS-1b, WS-2b, live WS-2a)
plus capx — the last-commit one-line protocol stands unchanged.

**Issued:** SCN-WS4b-r2, SCN-MX-R-r2 (both verbatim relaunches).
**Cards:** none ruled; all open. **One new routing item, not a card:** the NYISO marker
re-declaration, which belongs to the owner and the capx director.

---

### r#3 — 2026-09-06, main HEAD `ea2733395077f15b365273032c8821f86b18b1fb`

*(PR #4891.)* Delta from the r#2 pin
`db8b6015`: **18 commits**, of which nine are SCN and the rest are capx D65 and owner-track
nyiso-196.

**WHY THIS REFRESH EXISTS: the desk's own r#2 PR would not merge.** `git merge-tree
origin/main HEAD` conflicted on `docs/handoffs/scenario-desk-ledger-2026-09.md` — SCN-WS0
edited the ledger's §1 row and §3 rows 6–7 on main while the desk's r#2 commit rewrote the
same sections. **Resolved by rebuild, per the charter's own instruction to recreate the branch
fresh off `origin/main` at every refresh:** this branch is `ea273339` + the r#2 content +
r#3, with **SCN-WS0's §3 edits taken over the desk's** wherever they overlap (the lane's
version is sourced to its own FINDING and is the better record) and the desk's structural
sections preserved. The plan file merged cleanly and its r#2 card-status and §9 blocks are
re-applied on top of main's SCN-WS0 additions. No content from either side was dropped.

**RE-GRADED BY CONTENT — the r#2 verdicts that moved:**

| lane | r#2 verdict | r#3 verdict | what changed |
|---|---|---|---|
| **SCN-WS0** | CHECKPOINT, 4 of 6 | **LANDED — all six items** | `e8c7072d` (5/6, the `scenario` registration kind grouped by campaign with a CO2 delta-vs-reference), `79034547` (6/6, the paired NEISO T0), `47ba0610` (**the G-E4 cap-row rider the desk was about to charter, closed by the lane itself**), `f6abf592` (slim artifacts). `FINDING-scn-ws0-2026-09-05.md` on main. Both arms registered under `scn-ws0-smoke`; 0 FAIL / 0 WARN on all 14 invariants per arm; 2.3 / 2.2 min, 3.31 / 2.94 GB. |
| **SCN-WS1a** | LANDED, **matrix duty NOT discharged** | **LANDED, duty DISCHARGED** | `717de664` mints the `carbon_price_path` and `policy_bundle` base rows plus a cell line in every shard — verified at the pin (2 rows present). `a147362b` scores the CAISO T0 pair against the precommit: every structural gate row passes. The r#2 finding was true at the r#2 pin and the lane repaired it on its own; recorded that way, not as a desk intervention. |
| **SCN-WS2a** | CHECKPOINT, items 1–2 | **CHECKPOINT — and LIVE** | Branch `claude/scn-ws2a-federal-ces-qm512t` carries two commits ahead of main: `73e5351f` (the 05-policy.md + G-S6 docstring legs) and `6e6449ab` (**the NEISO T0 PRECOMMIT, pushed before the solve**, exactly as rule 29 requires). The lane is working its owed items now. |
| **SCN-WS3a / SCN-WS4a** | LANDED | LANDED, unchanged | — |

**THE SUBSTANTIVE RESULT OF THE WEEK — carbon leakage, measured.** SCN-WS0's exercising T0 is
the first case run through the new emissions surface, and it is not a plumbing result. A
$25/tCO2 adder cuts NEISO's modeled in-ISO CO2 by **−2.71 Mt (−16.6 %)** and simultaneously
raises `import_co2_mt_reported` by **+1.85 Mt**, *all of it on one rung* — `NYISO_CT_peak`,
+4.32 TWh, while both firm Hydro-Québec seams barely move. On the scored `emissions_mt` basis
the case reads as a 16.6 % cut; with the disclosure line beside it the modeled net is nearer
**−0.85 Mt (−5.2 %)**. And 0.428 t/MWh is the CARB *unspecified* default for a seam with no
derived EF — at a gas-CT-realistic 0.53, which is what the rung is named for, the net shrinks
again to **≈ −0.42 Mt**. This is G-E3 (plan §2.5) measured on a real case for the first time.
Three consequences the desk carries forward, all now written into the lanes:
1. **Every campaign delta is read with the import line beside it, per ISO — never a generic
   sentence.** Folded into SCN-WS1b's charter as a deliverable, since it is the lane that runs
   all six ISOs.
2. **The NEISO seam EF is now a number with a magnitude attached, not a placeholder.** It
   attaches to card D-4 as a second, sharper instance of the same provenance question.
3. The lane also found and fixed, in the same commit, that **export sinks share the `import`
   fuel type and dispatch negative**, so the import CO2 line was differencing them against
   imports — an unearned offset, now clamped rather than netted. Inert on this T0; fixed
   before it was not.

**WITHDRAWALS — three r#2 charters, none dispatched, none re-issued.** The charter forbids
re-issuing a lane that already landed, and the capx twin-check doctrine forbids building a
twin of a live lane:
- **SCN-WS0-R — WITHDRAWN.** Its entire scope (items 5–6, rider A the G-E4 cap-row export,
  rider A the G-E4 cap-row export) is on main. **Rider B is the one exception and it is
  CHECKED, not assumed: `results/cache.py` has not changed since the r#2 pin**, so the
  cache-epoch entry SCN-WS4a routed — recording that MISO forecast bundles are stale at the
  same key after the DC-share change — is still outstanding. It is one ledger entry, not a
  lane: **re-assigned to SCN-MX-R**, whose scope is widened by exactly this one file, stated
  in its charter and here in §4.
- **SCN-WS2a-R — WITHDRAWN.** SCN-WS2a is live with a pushed PRECOMMIT. Dispatching -R now
  would be the twin the D60-R2 precedent exists to prevent. If SCN-WS2a goes silent for two
  refreshes, the relaunch protocol applies then — not now.
- **SCN-MX-R — NARROWED, not withdrawn.** Its carbon half is done. What survives is real and
  unowned: `federal_ces_target_by_year` and `federal_ces_acp_usd_per_mwh` are still absent
  from the matrix at this pin, **and `check_mechanism_matrix.py` still exits 0** — so the
  duty-(c) enforcement gap is confirmed across two pins, not a one-off. The CES row itself
  belongs to live SCN-WS2a (rule 28(b): the session that tests the mechanism stamps it), so
  MX-R diagnoses the gate and stamps the row **only if** WS-2a lands without it.

**NEWLY UNBLOCKED, ISSUED THIS REFRESH.** WS-0 item 5 was the single blocker on both:
- **SCN-WS1b** — the six-ISO carbon paired probe + the NEISO/ERCOT T1-F ladder. Card D-1 is
  still open, so it runs the **reduced form** its charter names (`--set carbon_price_delta=25`
  rather than `carbon_price_path=mid`), and says so in its PRECOMMIT.
- **SCN-WS2b** — the premium-ladder re-prove at HEAD posture + the national clearing script.
  Independent of SCN-WS2a and SCN-WS2a-R; it consumes committed legs, not the target row.

**SCN-WS4b — RE-EMITTED VERBATIM, not graded lost.** Issued at r#2; no branch and no PR at
r#3. That is **one** refresh, and the charter's LOST threshold is two. Every r#1 lane launched
within hours, so the practical read is that it was never dispatched — the capx relaunch
doctrine for exactly this case is *ask, re-emit verbatim, do not grade lost*, and that is what
this refresh does. If it is absent again at r#4 it is LOST and gets a `-r2` stem.

**Capx deconfliction (D65 landed since r#2).** `4b28c93f` — capx D65 minted its own
mechanism-matrix row and a `U` cell in all six shards, i.e. **the capx track is writing the
matrix tree right now**. The last-commit one-line protocol is load-bearing for every SCN lane
this refresh; SCN-MX-R in particular must rebase immediately before its single stamping
commit. D65's code scope (`capacity_evolution/ccs.py` and the CCS cost anchors) touches no SCN
region. D60-R2 still unreported.

**Issued:** SCN-WS1b, SCN-WS2b, SCN-MX-R (narrowed), SCN-WS4b (re-emitted).
**Cards:** none ruled; all open, unchanged from r#2 except that WS-0's leakage number attaches
to D-4 as a second instance.

---

### r#2 — 2026-09-05, main HEAD `db8b6015a1534873dac50ddda0dce9372d099305`

`db8b6015` = PR #4885. Delta from the r#1 pin `d01ab8b0`: **111 commits**, of which the SCN track
contributed five merged PRs (#4853 desk, #4856/#4860/#4867 WS-1a, #4857/#4859 WS-3a, #4863 WS-4a,
#4869 WS-0, #4870 WS-2a). The rest is owner-track backcast (caiso-252 → CAISO keeper CALIBRATED,
miso-220 → MISO keeper CALIBRATED, nyiso-195/196, NEISO/PJM touchpoints), capx r#41 + D61/D64, and
CI plumbing (Y-13/Y-14).

**Graded BY CONTENT — every wave-1 lane:**

| lane | verdict | what is on main | what is owed |
|---|---|---|---|
| **SCN-WS1a** | **LANDED (complete under its gate)** | Phase-0 trajectory table + machine-readable JSON/py/txt (`docs/handoffs/scn-ws1a/`), items 2+3 (G-C2 `spec.py` corridor adder off the resolver; G-C3 membership-weighted column at `assemble_mc`), item 4 pre-declared, `FINDING-scn-ws1a-2026-09-05.md` incl. the D-1 evidence memo §6 | **item 1 correctly NOT executed** (D-1 open — the gate worked). **Matrix duty NOT discharged** (§below). Its §4.3 routes the cap-row slack/dual export to WS-0 as a G-E4 rider. |
| **SCN-WS3a** | **LANDED** | `voluntary-clean-demand-design-memo-2026-09-05.md`, 8 sections + 5 owner boxes (D-3, new D-3b, new D-3c, the D-6 brief, the D-2 voluntary sub-levels) + Addendum A | nothing. **Launched twice** — `…-s8iukw` and `…-9f1you` both ran the charter; the second merged with an add/add resolution as a cross-check addendum and reports no divergence. Recorded, not a fault of either lane: the desk issued one stem and the harness provisioned two. |
| **SCN-WS4a** | **LANDED** | ERCOT verified already-populated since 2026-07-21 (plan §2.4's "only for PJM" line was **stale**, corrected in-lane); MISO shares from 2026 LTLF slide 21 validated on the deck's own totals (9.6 TWh 2026, 266 TWh 2046, ~58 % Central); NEISO `{}` re-confirmed against the 2026 CELT with the arithmetic written out; `FINDING-scn-ws4a-2026-09-05.md` §4 = the D-4 gap list | nothing in scope. Routes **one cache-epoch entry** (`results/cache.py`, WS-1a's region) it correctly refused to write. |
| **SCN-WS0** | **CHECKPOINT — 4 of 6 items** | (1/6) emissions grain, (2/6) matrix frame + `report_scenario_deltas.py`, (3/6) `collate_scenario_campaign.py`, (4/6) the six-ISO scenario YAML set + `configs/scenario_campaign_matrix.yaml` + the `--set` override, plus `PRECOMMIT-scn-ws0-t0-2026-09-05.md` | **item 5** (the `scenario` kind on `register_forecast_run.py` + the campaign grouping / delta sparkline — verified absent) and **item 6** (the paired NEISO T0 through the new tables, both arms registered under campaign `scn-ws0-smoke`). No `FINDING-scn-ws0`. |
| **SCN-WS2a** | **CHECKPOINT — items 1–2** | one commit: the federal CES target row on the clean-tier family, the `rows.py:1346` coupling relaxation (WS-3b's precondition, delivered), `federal_ces_target_by_year` + `federal_ces_acp_usd_per_mwh` with `__post_init__` guards and cache-key registration at `None` | **item 3** (the three postures documented + tested), **item 4** (the NEISO 2026 T0 probe — no PRECOMMIT, no registration), **item 6** (matrix), `docs/codebase/05-policy.md` + the `constraints.py` docstring (G-S6), no `FINDING-scn-ws2a`, scorecard row unmoved. |

**THE FINDING OF THIS REFRESH — two undischarged matrix duties, one of them claimed as done.**
Grep at the pin over `docs/codebase-site/data/mechanism-matrix.js` and all six shards:

- `carbon_price_path` — **0 rows, 0 cells** (one incidental prose mention inside an unrelated
  NYISO note). `policy_bundle` — **0 rows, 0 cells**. Yet the ledger §3 row-5 Carbon cell, edited
  by SCN-WS1a itself, reads *"stamped (`carbon_price_path` + `policy_bundle` rows minted at
  WS-1a)"*. `git log --grep=SCN-WS1a -- docs/codebase-site/data/` returns **nothing**: the lane
  never committed to that tree. The claim is corrected in §3 below **against the lane's own
  record**, which is what grading by content is for. Rule 28 duty (b) undischarged.
- `federal_ces_target_by_year` / `federal_ces_acp_usd_per_mwh` — two solve-affecting
  `ScenarioConfig` fields added by SCN-WS2a with **no base row and no cell in any shard**. Rule 28
  duty (c) says that row belongs in the same PR and CI enforces it — **yet
  `scripts/check_mechanism_matrix.py` exits 0 at the pin** (warnings only, all pre-existing anchor
  drift). So the CI half that is supposed to catch a new field without a row **did not fire**.
  That is a gate defect, not an SCN mechanism question, and `scripts/` is not this desk's to edit:
  **routed** to SCN-MX-R to diagnose and report, and to the capx/audit track to fix if the repair
  is in the checker.

**Branch-stem divergence, recorded so §5 reconciles.** Every lane was provisioned by the harness
on its own branch name rather than the stem the desk issued (`scn-ws0-k7m2-8743yi`,
`scn-ws1a-carbon-d1-eupbi5`, `scn-ws2a-federal-ces-qm512t`, `scn-ws3a-voluntary-demand-{s8iukw,
9f1you}`, `scn-ws4a-datacenter-shares-yf7wvi`). WS-4a's FINDING flags it explicitly. No collision
resulted; §5 now records both the issued stem and the realized branch, and future issuance treats
the stem as advisory.

**Graded by content — capx deconfliction (capx r#41, HEAD `5cc1e7ce`):** D61 and D64 **landed**
and each relocated its object (the PJM D57 price ratio is the going-forward bar + census, not the
E&AS operand; the CCS carbon-0 closure rests on an **uncited** `ccs_retrofit_vom_adder` 8.0,
2.7–3.6× every published basis) → **D62 and D65 ISSUED** (D65's branch is live). **D60-R2: nothing
since #4824, status ASKED, not graded lost.** Files: D62/D65 are capacity-evolution and CCS
cost-leg lanes (`capacity_evolution/ccs.py`, `new_entry.py`, `constants.py`'s CCS anchors);
D60-R2 still holds `scripts/forecast_verdict.py` + `frontend/data/forecast/`. **No collision with
any r#2 SCN lane** — but note SCN-WS4b and SCN-MX-R both append to matrix shards, so the
last-commit protocol binds harder than ever (capx parity is RED on two unmapped bundles and the
owner's backcast track promoted two keepers today).

**Wave-2 unblocking, measured against the actual preconditions:**
- **SCN-WS1b** — BLOCKED. Its charter registers twelve arms; the `scenario` registration kind is
  WS-0 item 5 and is not on main.
- **SCN-WS2b** — BLOCKED, same reason (it registers ladder legs).
- **SCN-WS4b** — **UNBLOCKED and ISSUED.** Everything it consumes landed in WS-0 items 2 and 4
  (`report_scenario_deltas.py`, `configs/scenario_campaign_matrix.yaml`) and WS-4a; it registers
  nothing, so item 5 does not gate it. Campaign-YAML ownership **transfers to it** (§4).
- **SCN-WS4c** — BLOCKED on WS-4b.
- **SCN-WS3b** — BLOCKED on card D-3, still open. Its two code preconditions are now MET
  (WS-2a's coupling relaxation, WS-4a's DC module).

**Issued:** SCN-WS0-R, SCN-WS2a-R, SCN-MX-R, SCN-WS4b (§5).
**Cards:** D-1 and D-3 RE-PRESENTED on new evidence; D-4 PRESENTED; D-2, D-6 stand.

---

### r#1 — 2026-09-05, main HEAD `d01ab8b0ea5e3c6e1a68c86f8daad1b4b6d605e9`

`d01ab8b0` = PR #4840 (`claude/miso-219-evening-scarcity-qrliuv`), Sat 2026-09-05 15:25:45
−0700. The plan was surveyed at `4d4dc6ce`; the delta to the pin is owner-track backcast work
(miso-219 and predecessors) plus capx records lanes — **no file in any wave-1 SCN region moved**,
so every plan §2 file:line citation is used as written and each lane re-verifies its own anchors
at its branch point (each prompt says so).

**Read this refresh:** CLAUDE.md; the plan entire (§1 definition of done, §2 per-mechanism
state, §3 workstreams, §3.5 case set, §4 constraints, §5/§5.1 sequencing + scorecard, §6 owner
boxes, §7 prompts, §8 findings); FF plan §2.1b (window cap + four-leg gate), §2.4 (budget
anchors + the `data/clean` prerequisite), §7; capx ledger top block + §1 scoreboard;
`docs/mechanism-testing-matrix.md` §5 and the six shards.

**Graded by content — SCN lanes:** none exist. `git ls-remote origin 'refs/heads/claude/scn-*'`
returns empty; no `FINDING-scn-*` doc on main; plan §5.1 unmoved from v1. This is the first
refresh, so nothing is LOST and no relaunch protocol applies.

**Graded by content — capx deconfliction (from capx r#40, HEAD `4d4dc6ce`):**

| capx lane | status | files it holds | collision with wave 1? |
|---|---|---|---|
| **D60-R2** | RUNNING (PR #4824) | `scripts/forecast_verdict.py` (the `_dof_ledger_row` builder + six new (ISO, field) rows), `frontend/data/forecast/` board + verdict re-scores, the finding | **NO** on `src/`; **SHARD-ADJACENT** — its re-scores can append to matrix shards. Mitigated by the last-commit protocol. |
| **D61** | ISSUED, unlaunched | docs only (PJM E&AS operand Phase 0) | no |
| **D64** | ISSUED r#40, unlaunched | docs only (CCS ΔFOM / capture VOM Phase 0) | no |
| **D58** | RELEASED, dispatch after D60 lands | `frontend/data/forecast/` PJM board t1f row; solves | **NO** on `src/`; WS-0 must not touch `program-status.json`. |
| **D63** | queued-named | MISO/CAISO DOF-row identification | no |
| **T3-NYISO-GOLDEN** | HELD (precondition lapsed) | — | no |

**Conclusion: no HOLD is required for any wave-1 lane.** The capx track's live writers are in
`scripts/forecast_verdict.py` and `frontend/data/forecast/`; wave 1's `src/` regions
(`policy/carbon.py`, `policy/cap_and_trade.py`, `policy/federal_ces.py`, `policy/clean_tiers.py`,
`model/lp/rows.py`, `model/interchange/spec.py`, `results/export.py|outputs.py|emissions.py`,
`src/market_sim/matrix.py`, `data/datacenter.py`, and the four named `runner.py` /
`scenarios.py` / `constants.py` regions) are unheld. The one live shared surface is the six
matrix shards, written by capx re-scores AND by the owner's backcast lanes several times a day
(`3eaf7918` caiso-252, `fe38a699` nyiso-194 both landed on 2026-09-05) — hence the protocol.

**Issued:** SCN-WS0, SCN-WS1a, SCN-WS2a, SCN-WS3a, SCN-WS4a (§5).
**Cards presented:** D-1, D-2, D-3, D-6.

---

## 1. Lane scoreboard

| lane | scope | status | branch | model | evidence / notes |
|---|---|---|---|---|---|
| **SCN-WS0** | Emissions grain (by fuel / by zone / import line / unserved) + multi-metric matrix frame + `report_scenario_deltas.py` + `collate_scenario_campaign.py` + the scenario YAML set + `--set` override + `scenario` registration kind; one paired NEISO T0 to exercise it | **LANDED r#3 — all six items** | `claude/scn-ws0-k7m2-8743yi` (merged, PRs #4869/#4877) | **Opus** | Completed itself between refreshes, **including the G-E4 cap-row rider the desk was about to charter**. T0 STOP gate PASS, 0 FAIL/0 WARN × 14 invariants per arm, both arms registered (`scn-ws0-smoke`). `FINDING-scn-ws0-2026-09-05.md`. **Its result is the leakage number** (§0 r#3). Unblocks WS-1b, WS-2b, WS-4b/c, WS-5. **SCN-WS0-R WITHDRAWN undispatched.** |
| **SCN-WS1a** | Federal carbon-price semantics (G-C1, gated on D-1) + the two seam defects (G-C2, G-C3) + the pre-declared `CAP-STATE-TIGHT` case | **LANDED r#3 (complete under its card gate, matrix duty discharged)** | `claude/scn-ws1a-carbon-d1-eupbi5` (merged, PRs #4856/#4860/#4867/#4887) | **Fable** | Items 2–4 + Phase 0 + the D-1 evidence memo; item 1 correctly withheld on the open card. **`717de664` minted the `carbon_price_path` + `policy_bundle` rows and a cell in all six shards** — the r#2 finding was true at its pin and the lane repaired it itself. `a147362b` scored the CAISO T0: every structural gate row passes. Item 1 remains the only thing D-1 blocks. |
| **SCN-WS2a** | The endogenous national CES **target** row (G-S1, G-S3) + the two new fields + the three state/federal postures | **CHECKPOINT r#4 — OWED, not lost** | `claude/scn-ws2a-federal-ces-qm512t` (all merged, PRs #4870/#4892) | **Fable** | Items 1–2, the docs legs (`73e5351f`) and the T0 PRECOMMIT (`6e6449ab`, pushed before the solve) all on main. **Still owed: the probe result, the postures tests, the FINDING, and the CES matrix row** (`federal_ces_target_by_year` absent from the matrix at three consecutive pins). Holds merged PRs → the relaunch protocol does NOT apply; SCN-WS2a-R stays withdrawn. |
| **SCN-WS3a** | Voluntary clean-demand **design memo** (no code, no solve) | **LANDED r#2** | `claude/scn-ws3a-voluntary-demand-{s8iukw, 9f1you}` (both merged, PRs #4857/#4859) | **Fable** | Memo + 5 owner boxes (D-3, new **D-3b**, new **D-3c**, the D-6 brief, the D-2 voluntary sub-levels) + a cross-check addendum. **Launched twice**; no divergence between the instances. |
| **SCN-WS4a** | DC zone shares for ERCOT + MISO; NEISO `{}` re-check; the D-4 constant-vs-published gap list | **LANDED r#2** | `claude/scn-ws4a-datacenter-shares-yf7wvi` (merged, PR #4863) | **Opus** | ERCOT already populated (plan §2.4 corrected); MISO populated + validated on published totals; NEISO `{}` re-confirmed; D-4 gap list presentable unedited. |
| **SCN-WS1b** | Six-ISO carbon paired T0 probe + NEISO/ERCOT T1-F ladder + the per-ISO leakage line | **RUNNING r#4** (owner-confirmed launch; no branch yet, normal inside one refresh — graded by content at r#5) | `claude/scn-ws1b-carbon-sixiso-h6rt` | **Opus** | UNBLOCKED by WS-0 item 5. Runs the **reduced form** (`--set carbon_price_delta=25`) while D-1 is open. Carries WS-0's leakage duty: the import line beside CO2, per ISO. |
| **SCN-WS2b** | Premium-ladder re-prove at HEAD posture + `scripts/ces_national_clearing.py` | **RUNNING r#4** (owner-confirmed launch; no branch yet — graded by content at r#5) | `claude/scn-ws2b-ces-ladder-clearing-p9wf` | **Opus** | UNBLOCKED by WS-0 item 5. Independent of live SCN-WS2a — it consumes committed premium legs, not the target row. |
| **SCN-WS0-R** | *(WS-0's owed half)* | **WITHDRAWN r#3, NEVER DISPATCHED** | — | — | Its entire scope landed on main between r#2 and r#3, riders included. Recorded so no successor re-issues it. |
| **SCN-WS2a-R** | *(WS-2a's owed half)* | **WITHDRAWN r#3, NEVER DISPATCHED** | — | — | SCN-WS2a is live with a pushed PRECOMMIT; dispatching -R would build the twin the D60-R2 precedent exists to prevent. If WS-2a is silent for two refreshes the relaunch protocol applies then. |
| **SCN-MX-R** | *(the r#2/r#3 stem)* | **LOST r#4 — NEVER LAUNCHED** | `claude/scn-mxr-matrix-duty-repair-j5tv` (burned) | — | No branch, no PR, two refreshes after issuance. Relaunch protocol applied; not re-graded as running. |
| **SCN-MX-R-r2** | Diagnose why `check_mechanism_matrix.py` exits 0 on a PR adding two `ScenarioConfig` fields with no row (now confirmed across **three** pins); the one verified-outstanding cache-epoch entry; the CES row **only if** SCN-WS2a lands without it | **RELAUNCHED r#4 (verbatim)** | `claude/scn-mxr2-matrix-duty-repair-t7bq` | **Fable** | `scripts/` stays un-edited: diagnose and route. |
| **SCN-WS4b** | *(the r#2/r#3 stem)* | **LOST r#4 — NEVER LAUNCHED** | `claude/scn-ws4b-loadhi-adequacy-b2np` (burned) | — | No branch, no PR, two refreshes after issuance. Relaunch protocol applied; not re-graded as running. |
| **SCN-WS4b-r2** | Pre-declared adequacy reading per ISO under LOAD-HI + the LOAD-HI / LOAD-HI-ORGANIC case comments + the "backstop-built" column + the per-ISO import-line expectation | **RELAUNCHED r#4 (verbatim)** | `claude/scn-ws4b2-loadhi-adequacy-x3mc` | **Fable** | Campaign-YAML ownership stands with it (§4). **The last thing blocking SCN-WS4c.** |
| **SCN-WS4c** | Six T0 LOAD-HI probes + NEISO/ERCOT T1-F | **BLOCKED (wave 2)** | — | Opus | WS-0 ✓, WS-4a ✓. **Blocked on SCN-WS4b-r2 alone.** |
| **SCN-WS3b** | Voluntary-demand build | **BLOCKED (wave 2) — on the CARD only** | — | Fable | Both code preconditions now MET (WS-2a's `rows.py` coupling relaxation landed and documents the second-consumer seam; WS-4a's DC module landed). Blocked solely on **D-3 + the memo's boxes D-3b/D-3c/D-2-voluntary**, all open. |
| **SCN-WS3c** | Voluntary-demand probe (ERCOT T0 → T1-F) | **QUEUED (wave 3)** | — | Opus | Precondition: WS-3b on main. |
| **SCN-WS5A-\<ISO\>** ×6 + **-SYNTH** | Stage A campaign, T1-F 2026–2030, all six ISOs | **QUEUED (wave 3)** | — | Opus | Precondition: WS-0, WS-1a/b, WS-2a/b, WS-4a/b/c on main; WS-3b/c on main **or** D-3 ruled NO (then VOL-\* and CES-P20+VOL-HI drop, with a ledger note). |
| **Stage B** | Full-horizon legs | **NOT ISSUABLE** | — | — | Needs card D-5 **and** an OPEN §2.1b gate for the named ISO at issuance. At the r#1 pin only NEISO is open. Re-check at issuance, never at planning. |

---

## 2. Owner cards

| card | question | status | recorded ruling |
|---|---|---|---|
| **D-1** | Federal carbon price on a program ISO: **replace** (today), **floor** (`max`), or **additive**? Recommendation: **floor** — *now with the measured consequence, and two sub-questions it raises*. | **RE-PRESENTED r#2 on new evidence** (WS-1a Phase 0 + memo §6) | — |
| **D-1(b)** | *(new, raised by the evidence)* Once the floor is in, `policy_bundle="tight"` is an exact **no-op** on CAISO/NYISO/NEISO — the RFF mid path never exceeds a program trajectory in any year. Should `tight` mean something else on a program ISO? | **PRESENTED r#2** | — |
| **D-1(c)** | *(new)* PJM's partial RGGI footprint under a federal floor — floor against what, when only part of the fleet faces the state program? | **PRESENTED r#2** | — |
| **D-2** | Campaign levels — carbon paths, CES premium ladder, **CES target schedule + ACP**, voluntary levels, load-high pairing. Recommendation: the plan's §3.5 table. The WS-3a memo box 5 now supplies the **voluntary sub-levels** (`s_base`, `f_commit`, the WTP ceiling) as a named part of this card. | **PRESENTED r#1**, unmoved r#2 | — |
| **D-3** | Is a voluntary clean-demand **scenario axis** admissible given ffr-5b's inadmissibility ruling on corporate PPA demand as a *driver*? Recommendation: **yes**, as a declared forecast-only publicly-anchored axis. | **RE-PRESENTED r#2** — the WS-3a memo §1 is now the brief | — |
| **D-3b** | *(memo box 2)* Does in-LP hourly (24/7) matching stay deferred to the isolated `scope2-lce-portfolio` tool? Recommendation: **yes, deferred**. | **PRESENTED r#2** | — |
| **D-3c** | *(memo box 3, NEW)* The eligible set — renewable-only by default (incl. offshore wind), carbon-free (nuclear/CCS) only as a labelled override; credit all eligible units or new builds only? | **PRESENTED r#2** | — |
| **D-4** | Fund the `load-forecast` curated intake? Recommendation: **defer** — and the lane's own list says the prize is the **empty electrification layers** (G-D4-4), not the growth rates. | **PRESENTED r#2** — `FINDING-scn-ws4a-2026-09-05.md` §4 is the list, presentable unedited | — |
| **D-5** | Per-campaign §2.1b grant for the NEISO scenario campaign (Stage B). | **HELD** — presented only with Stage A's measured cost table on the dashboard. | — |
| **D-6** | Attribute netting between a federal CES row and a voluntary-demand row. Recommendation: **counts toward**, report both. | **PRESENTED r#1** | — |

Rulings are recorded verbatim and numbered **S1, S2, …** here and appended to the plan's §6 row
as `RULED <date>: …` in the same refresh commit.

---

## 3. Readiness scorecard (the plan's §5.1, kept current here)

State at r#1 = plan v1, unmoved. Each landing lane updates BOTH this table and the plan's §5.1.

| Criterion (plan §1) | Carbon | CES premium | CES target | Voluntary | Load-HI | Emissions |
|---|---|---|---|---|---|---|
| 1 expressible in committed config | yes (G-C1 PROVEN at WS-1a Phase 0: `tight` is a cut of $16–$102/t on CAISO/NYISO/NEISO in all 25 yrs, and a floor makes it an exact **no-op** there — repair gated on D-1; `FINDING-scn-ws1a-2026-09-05.md` §0.1/§6) | yes | **yes** (SCN-WS2a: `federal_ces_target_by_year` + `federal_ces_acp_usd_per_mwh`; illustrative level, D-2 open) | **no** | partial — **siting sourced** for ERCOT/PJM/MISO (SCN-WS4a), named case now with **SCN-WS4b** | **yes r#2** — six-ISO REF bases + `scenario_campaign_matrix.yaml` + the `--set` override (WS-0 item 4) |
| 2 reaches dispatch + deployment | yes (G-C2 + G-C3 closed at WS-1a; cap-row dual NOT exported — G-E4 rider now assigned to **SCN-WS0-R**) | yes | **yes** (SCN-WS2a: the row → dispatch; dual → the existing `max()` screen seam; deployment leg not exercised by the 1-yr T0) | **no** | yes | — |
| 3 paired probe right-signed, per ISO | NEISO only | ERCOT only (July posture) | NEISO only, escape regime (dual = ACP $50 exactly; CO2 +2e-4 reported not smoothed — `FINDING-scn-ws2a-2026-09-05.md` §4.3) | **no** | **no** | — |
| 4 backcast byte-identity | yes (WS-1a: no key moves; keeper + forecast key list, FINDING §5) | yes | yes (SCN-WS2a: six keeper keys byte-identical, FINDING §5) | — | yes | — |
| 5 matrix duty | stamped — `carbon_price_path` + `policy_bundle` base rows and a cell in every shard at `717de664` (on main). The r#2 "NOT stamped" reading was true at `db8b6015`; the lane's claim ran one PR ahead of its commit and the lane closed it itself. Verified on disk by SCN-MX-R-r2 (r#4, `FINDING-scn-mxr-2026-09-06.md` §5). | stamped | stamped (`federal_ces_target` row + six cells, SCN-WS2a last commit) | — | stamped | — |
| 6 emissions grain | by fuel / by zone | by fuel / by zone | by fuel / by zone | by fuel / by zone | by fuel / by zone | **G-E1..E5 CLOSED** (SCN-WS0, all six items landed 2026-09-05); G-E6 / G-E7 stay OPEN as declared disclosure items |
| 7 registered probes on dashboard | NEISO FC-6 pair | pruned (G-S5) | NEISO T0 pair `neiso-2026-2026-scn-ws2a-neiso-2026-t0-{ref,target}` (kind `scenario`) | — | none | `scn-ws0-smoke` REF/CARB pair |

**Open lane assignments against the scorecard:** ~~WS-0 → the Emissions column entire (criterion
6) + criterion 1's harness half~~ — **LANDED 2026-09-05, ALL SIX ITEMS**, G-E1..E5 closed and
criterion 1's harness half with them; G-E6/G-E7 remain open as declared disclosure items
(`docs/handoffs/FINDING-scn-ws0-2026-09-05.md`); WS-1a → Carbon row 1 (the G-C1 defect) and rows 4/5; WS-1b →
Carbon rows 3/7; WS-2a → the CES-target column rows 1/2/4/5 and its probe half of row 3; WS-2b →
CES-premium rows 3/7; WS-3a → nothing (memo); WS-4a → Load-HI row 1 (partial → the siting half)
— **LANDED 2026-09-05**: MISO populated from the 2026 LTLF regional DC decomposition, ERCOT
verified already-populated (the plan §2.4 "only for PJM" line was stale and is corrected), NEISO
`{}` re-confirmed with its arithmetic; the named case remains SCN-WS4b's and is NOT claimed.
The D-4 gap list is `docs/handoffs/FINDING-scn-ws4a-2026-09-05.md` §4, presentable unedited; that
FINDING §6 routes one cache-epoch ledger entry (MISO forecast bundles stale at the same key) that
SCN-WS4a may not write, `results/cache.py` being another lane's region.

---

## 4. Collision register (file → owning lane → wave)

**Wave-1 shared-file protocol** (written verbatim into every wave-1 prompt):

1. `config/scenarios.py` and `runner.py` are touched by WS-1a and WS-2a in the **named disjoint
   regions ONLY**. Any edit outside your region is a **STOP** — route it to SCN-DESK in your
   FINDING; do not widen.
2. The six matrix shards (`docs/codebase-site/data/mechanism-matrix/<ISO>.js`) and
   `docs/codebase-site/data/mechanism-matrix.js`: make the edit your **LAST commit**, after
   `git fetch origin main` + rebase, as **one appended cell line per ISO**, so any conflict is
   one line. This is not advisory — capx D60-R2's re-scores and the owner's backcast lanes
   append to these files several times a day (`3eaf7918`, `fe38a699` both on 2026-09-05).
   Merge order if WS-1a and WS-2a are both ready: **WS-1a first, WS-2a rebases.** CI
   (`scripts/check_mechanism_matrix.py`) enforces that a new `ScenarioConfig` field carries its
   base row + a cell line in every shard **in the same PR** (rule 28 duty c).
3. **`configs/scenario_campaign_matrix.yaml` OWNERSHIP TRANSFERS to SCN-WS4b at r#2** — WS-0's
   YAML work (item 4) landed and its owed items 5–6 do not touch the file. SCN-WS0-R must not
   edit it.
3a. **MATRIX-TREE PROTOCOL, AMENDED r#3.** The r#2 freeze is **lifted** — SCN-WS1a minted its
   own rows and cells, so there is no longer one repair lane holding the tree. The standing
   rule returns to protocol item 2 (**last commit, after rebase, one appended line per ISO**),
   and it binds harder than at r#2: capx D65 stamped its own row and six cells at `4b28c93f`,
   so the capx track is an active concurrent writer. Live SCN-WS2a stamps the CES row itself
   (rule 28(b) — the session that tests the mechanism stamps it); SCN-MX-R stamps it **only
   if** WS-2a lands without it. SCN-WS1b and SCN-WS2b stamp their own cells, last commit.
4. **Nobody touches `frontend/data/forecast/program-status.json`** — it is the capx board,
   written by D60-R2 and D58.

| file / region | owning lane | wave | note |
|---|---|---|---|
| `src/market_sim/results/export.py`, `results/outputs.py`, `results/emissions.py` | SCN-WS0 | 1 | |
| `src/market_sim/matrix.py`, `scripts/collate_full_horizon.py` | SCN-WS0 | 1 | |
| new `scripts/report_scenario_deltas.py`, new `scripts/collate_scenario_campaign.py` | SCN-WS0 | 1 | WS-4b adds the "backstop-built" column to the former **after** WS-0 lands. |
| `scripts/run_full_horizon.py`, `scripts/run_ces_leg.py` | SCN-WS0 | 1 | **the `--set` override ONLY** |
| `scripts/register_forecast_run.py`, the forecast dashboard pages | SCN-WS0 | 1 | NOT `frontend/data/forecast/program-status.json` |
| `configs/scenarios/*`, `configs/scenario_campaign_matrix.yaml` | SCN-WS0 | 1 | sole writer this wave |
| `src/market_sim/policy/carbon.py`, `policy/cap_and_trade.py`, `config/scenario_resolvers.py` | SCN-WS1a | 1 | |
| `src/market_sim/model/interchange/spec.py` — **the one carbon-adder line (~:1931)** | SCN-WS1a | 1 | |
| `runner.py` — **REGION: the `assemble_mc` call site (~:2561-2575)** | SCN-WS1a | 1 | |
| `config/scenarios.py` — **REGION: the D34 guard in `__post_init__` (~:15572)** | SCN-WS1a | 1 | |
| `src/market_sim/results/cache.py` — **one epoch entry** | SCN-WS1a (LANDED) → SCN-WS0-R (WITHDRAWN) → **SCN-MX-R at r#3** | 1–3 | The WS-4a-routed entry (MISO forecast bundles stale at the same key after the DC-share change) did **not** land — verified: the file is unchanged since `db8b6015`. MX-R's scope is widened by this one file only, and it writes a ledger entry, never a key. |
| `tests/unit/policy/test_cap_and_trade.py`, `test_carbon_price_below_base_guard.py` | SCN-WS1a | 1 | |
| `src/market_sim/model/lp/rows.py` | SCN-WS2a | 1 | WS-3b is the next writer (wave 2), **after** WS-2a merges. |
| `src/market_sim/policy/federal_ces.py`, `policy/clean_tiers.py` | SCN-WS2a | 1 | |
| `runner.py` — **REGION: RPS/clean-row arming + dual plumbing (~:1195-1229, :2851-2864, :4484-4521)** | SCN-WS2a | 1 | |
| `config/scenarios.py` — **REGION: the `federal_ces_*` block (~:3084-3157) + its `__post_init__` guard (~:15584)** | SCN-WS2a | 1 | |
| `docs/codebase/05-policy.md`, `policy/constraints.py` docstring (G-S6) | SCN-WS2a | 1 | |
| `docs/handoffs/voluntary-clean-demand-design-memo-2026-09-05.md` (new) | SCN-WS3a | 1 | memo only |
| `config/constants.py` — **REGION: `DATACENTER_ZONE_SHARE` / `DATACENTER_ADDITIONS_MW` only** | SCN-WS4a | 1 | `VOLUNTARY_*` anchors are WS-3b's separate region, wave 2. |
| `src/market_sim/data/datacenter.py`, `tests/unit/data/test_datacenter.py` | SCN-WS4a | 1 | WS-3b's DC-linked volume helper is the next writer, **after** WS-4a merges. |
| the six matrix shards + `mechanism-matrix.js` | **SCN-MX-R ONLY until it merges**; then ALL, last commit only | 1–3 | see protocol items 2 and 3a |
| `scripts/register_forecast_run.py`, `configs/scenarios/*` | SCN-WS0 (LANDED) → **SCN-WS0-R** | 1–2 | |
| `configs/scenario_campaign_matrix.yaml` | SCN-WS0 (LANDED) → **SCN-WS4b** | 1–2 | transfer recorded at r#2 |
| `scripts/check_mechanism_matrix.py` | **NOBODY on the SCN track** | — | the duty-(c) CI gap is diagnosed and reported by SCN-MX-R and routed to the capx/audit track; `scripts/` is not this desk's to repair |
| `scripts/forecast_verdict.py`, `frontend/data/forecast/program-status.json` | **capx D60-R2 / D58** | — | **no SCN lane may touch these** |

---

## 5. Issuance record

Stems are recorded so a relaunch (`…-r2`) can never collide with the original.

| refresh | lane | model (id) | branch stem issued | **branch realized** | data profile | plan §7 body used |
|---|---|---|---|---|---|---|
| r#1 | SCN-WS0 | **Opus** `claude-opus-5` | `claude/scn-ws0-k7m2` | `claude/scn-ws0-k7m2-8743yi` | `neiso` | §7 "WS-0", verbatim |
| r#1 | SCN-WS1a | **Fable** `claude-fable-5-1` | `claude/scn-ws1a-p4qd` | `claude/scn-ws1a-carbon-d1-eupbi5` | `caiso` | §7 "WS-1a", verbatim + the D-1 gate split (item 1 conditional) |
| r#1 | SCN-WS2a | **Fable** `claude-fable-5-1` | `claude/scn-ws2a-t9xb` | `claude/scn-ws2a-federal-ces-qm512t` | `neiso` | §7 "WS-2a", verbatim |
| r#1 | SCN-WS3a | **Fable** `claude-fable-5-1` | `claude/scn-ws3a-r6vn` | `claude/scn-ws3a-voluntary-demand-{s8iukw, 9f1you}` **(twice)** | `code` | §7 "WS-3a", verbatim |
| r#1 | SCN-WS4a | **Opus** `claude-opus-5` | `claude/scn-ws4a-h3zc` | `claude/scn-ws4a-datacenter-shares-yf7wvi` | `all` | §7 "WS-4" **items 2 and 5 only** (items 1/3/4 split to WS-4b/WS-4c, wave 2) |

**r#2 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | body used |
|---|---|---|---|---|---|
| r#2 | SCN-WS0-R | **Opus** `claude-opus-5` | `claude/scn-ws0r-registration-t0-m4qk` | `neiso` | plan §7 "WS-0" **items 5 and 6 only** + the G-E4 cap-row rider (routed from WS-1a §4.3) + the WS-4a cache-epoch entry |
| r#2 | SCN-WS2a-R | **Fable** `claude-fable-5-1` | `claude/scn-ws2ar-ces-postures-probe-w8dr` | `neiso` | plan §7 "WS-2a" **items 3 and 4** + the G-S6 doc legs; matrix withheld to SCN-MX-R |
| r#2 | SCN-MX-R | **Fable** `claude-fable-5-1` | `claude/scn-mxr-matrix-duty-repair-j5tv` | `code` | not a plan §7 body — a rule-28 repair charter written at r#2 from the refresh's own finding |
| r#2 | SCN-WS4b | **Fable** `claude-fable-5-1` | `claude/scn-ws4b-loadhi-adequacy-b2np` | `all` | plan §7 "WS-4" **items 1 and 3** (the split recorded at r#1), no solve |

**r#3 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | body used |
|---|---|---|---|---|---|
| r#3 | SCN-WS1b | **Opus** `claude-opus-5` | `claude/scn-ws1b-carbon-sixiso-h6rt` | `all` | plan §7 "WS-1b", verbatim + the reduced-form D-1 gate + WS-0's per-ISO leakage duty |
| r#3 | SCN-WS2b | **Opus** `claude-opus-5` | `claude/scn-ws2b-ces-ladder-clearing-p9wf` | `ercot` then `neiso` | plan §7 "WS-2b", verbatim |
| r#3 | SCN-MX-R | **Fable** `claude-fable-5-1` | `claude/scn-mxr-matrix-duty-repair-j5tv` | `code` | r#2 repair charter, **narrowed at r#3** to the CI-gate diagnosis + a conditional CES stamp |
| r#3 | SCN-WS4b | **Fable** `claude-fable-5-1` | `claude/scn-ws4b-loadhi-adequacy-b2np` | `all` | r#2 charter **re-emitted verbatim** |

**r#4 issuance (relaunches).**

| refresh | lane | model (id) | branch stem issued | data profile | body used |
|---|---|---|---|---|---|
| r#4 | SCN-WS4b-r2 | **Fable** `claude-fable-5-1` | `claude/scn-ws4b2-loadhi-adequacy-x3mc` | `all` | the r#3 charter **verbatim** |
| r#4 | SCN-MX-R-r2 | **Fable** `claude-fable-5-1` | `claude/scn-mxr2-matrix-duty-repair-t7bq` | `code` | the r#3 narrowed charter **verbatim** |

**Burned stems, never to be reused:** `claude/scn-ws4b-loadhi-adequacy-b2np`,
`claude/scn-mxr-matrix-duty-repair-j5tv` (LOST at r#4), plus the r#3 withdrawals below.

**Withdrawn at r#3, never dispatched:** SCN-WS0-R (`claude/scn-ws0r-registration-t0-m4qk`) and
SCN-WS2a-R (`claude/scn-ws2ar-ces-postures-probe-w8dr`). Their stems are burned and must not be
reused; a future lane needing that scope takes a new stem.

**Branch stems are ADVISORY, not binding** (r#2): every r#1 lane was provisioned by the harness on
its own branch name. The stem's purpose — stopping a relaunch from colliding with an original — is
served by the realized-branch column above, which every future relaunch must check first.

### 5.1 Model assignment — the standing rule and the r#1 assignments

**The rule, in force for every SCN lane at every refresh.** Rule 27 `[R-PUSH]` second half: any
session whose scope writes core infrastructure — anything under `src/market_sim/`,
`scripts/run_*.py` / `scripts/score_*.py`, `CLAUDE.md`, `model-methodology-spec.md`, or
`.github/workflows/` — is **Opus or Fable, never Sonnet**. The desk charter tightens this to
**no Sonnet on any SCN lane at all**, docs-only lanes included, so rule 27 is never the binding
constraint here — the plan's own label is. Within Opus/Fable the split follows the director's
r#20 doctrine, restated at plan §3: **`[FABLE]` for structural / adjudication work** (a design
whose shape is still being decided, a semantics change, an argument against a standing ruling)
and **`[OPUS]` for pre-declared execution** (a charter whose deliverables and gates are already
written down and whose job is to carry them out exactly).

| lane | label | model id | why this side of the split |
|---|---|---|---|
| SCN-WS0 | `[OPUS]` | `claude-opus-5` | Execution. Six enumerated deliverables, each with its own commit and its own trivial-first test; the paired T0's gate is arithmetic (by-fuel CO2 sums to `emissions_mt`). Nothing here is a judgment call. Writes `src/` + `scripts/` → rule 27 binds. |
| SCN-WS1a | `[FABLE]` | `claude-fable-5-1` | Adjudication. It changes what an existing registered field *resolves to* on three ISOs, argues the D-1 evidence memo the owner rules on, and must prove byte-identity across every keeper key. Writes `src/` → rule 27 binds. |
| SCN-WS2a | `[FABLE]` | `claude-fable-5-1` | Structural. A new LP row family, a coupling relaxation (`rows.py:1346`) that a later lane inherits, two new fields with a mutual-exclusion guard, and three postures to document. Writes `src/` → rule 27 binds. |
| SCN-WS3a | `[FABLE]` | `claude-fable-5-1` | Pure adjudication — the memo argues, line by line, that a declared scenario axis is a different admissibility class from the driver `ffr-5b` ruled out. Docs-only, so rule 27's letter would permit Sonnet; **the charter forbids it**, and this is the least Sonnet-shaped task in the wave. |
| SCN-WS4a | `[OPUS]` | `claude-opus-5` | Execution. Transcribe published siting geography with citations, hold shares to 1.0, re-check one immateriality arithmetic, enumerate a gap list. Rule 14 provenance work with a fixed shape. Writes `config/constants.py` → rule 27 binds. |

**Queued lanes carry their labels forward** (assigned now so a relaunch cannot drift): SCN-WS1b
Opus, SCN-WS2b Opus, SCN-WS4b **Fable** (it is the adequacy *adjudication* — it pre-declares how
each ISO's high case is read, and pre-declaring a reading is the Fable half of plan §3 WS-4),
SCN-WS4c Opus, SCN-WS3b **Fable** (build-from-a-signed-design, but it is the first writer of a
new mechanism), SCN-WS3c Opus, SCN-WS5A-\<ISO\> ×6 + -SYNTH Opus.

**The desk itself.** The charter assigns **Fable** to SCN-DESK; this session is configured
`claude-opus-5` and the serving model may differ again. Recorded against interest — it is a
divergence from the charter, it affects only adjudication tone and not any lane's assignment,
and a successor desk session should be opened on Fable.

**Splits and gates applied to the plan's §7 bodies (never widenings):**
- WS-1a: plan item 1 is conditional on card D-1 reading FLOOR; unsigned → items 2–3 + the
  Phase-0 trajectory table + the D-1 evidence memo, then stop.
- WS-4: the plan's single §7 "WS-4" prompt is split three ways by the charter's wave plan —
  items 2+5 to **WS-4a** (wave 1), items 1+3 to **WS-4b** (wave 2, Fable), item 4 to **WS-4c**
  (wave 2, Opus) — because items 1 and 4 depend on WS-0's campaign YAML and harness, which do
  not exist yet.
- No other lane's body was edited.
