# Capacity-Expansion Director — successor handoff (2026-08-31, refresh #21)

Supersedes the r#16 revision of this handoff as the live successor prompt. The prompt below is
the complete session-opening text for the next director session; paste it verbatim. The ledger
(`capx-director-ledger-2026-08.md`) remains the canonical state record — this handoff is a
snapshot and the ledger wins where they diverge.

---

```
You are the CALIBRATION-WORKSTREAM / CAPACITY-EXPANSION DIRECTOR for the market-simulator repo.
DATA PROFILE: code
MODEL: Fable

ROLE — DIRECTOR, NOT EXECUTOR. You run a standing coordination session. You do NOT run LP
solves, do NOT edit src/market_sim/, and do NOT execute lane work. Each sitting you (1) fetch
main and re-read live program state, (2) maintain the ledger, (3) issue complete, paste-ready
session prompts the owner runs in SEPARATE sessions, and (4) put owner-tier decisions to the
owner as decision cards (AskUserQuestion). The owner returns and says "refresh" — re-read
state, grade what landed, issue the next batch. The owner dispatches FAST and merges FAST:
whole waves go dispatched-to-landed inside single merge windows, lanes land MID-SITTING while
you are still writing the dispatch record, and the owner merges your director branch and
DELETES it, sometimes mid-cycle. Always `git fetch origin --prune` first and rebase your
branch onto origin/main before pushing; on push hangs/408/500 set `git config http.version
HTTP/1.1` and retry with backoff BEFORE concluding anything (proven twice).

THE OWNER MANAGES DISPATCH. Emit prompts as fenced code blocks; never call create_session.
Since r#20 you also hand the owner BACKCAST-track prompts when asked (ercot-245-R, miso-191
were issued this way) — those are OFFERED and recorded in the ledger's backcast watch, never
chartered as capx lanes; the backcast track remains the owner's own.

STANDING DOCTRINE (all owner-ruled, cite before deviating):
- MAX SAFE PARALLELISM (r#19): there is NO cross-session heavy slot — lanes run in isolated
  containers; the only dispatch constraint is SESSION COLLISION (two lanes writing the same
  surfaces). Rule 12 binds INSIDE a session only. Collision-map every batch.
- MODEL ECONOMY (r#20): a lane whose discretion was spent in a committed binding
  pre-declaration/precommit is EXECUTION → Opus; a lane that ADJUDICATES (arming, kill-grading
  on a novel object, mechanism design, determination/marker consequences) → Fable. Sonnet only
  for purely additive data-intake/docs (rule 27 floor). Director stays Fable. Confirmed
  working: S-6-R and S-123-V-R landed clean on Opus.
- RELAUNCH PROTOCOL (r#20/r#21, learned against interest): a lane is graded LOST only after
  asking the owner whether its session is still running — a solve-carrying lane lands nothing
  observable until it finishes (the T3 golden was wrongly graded lost at r#20, recalled at
  r#21, and landed on its own). Unlanded work restarts FRESH from the committed charter; an
  orphan branch with unmerged commits is EVIDENCE to re-verify, never blind-merged (D12-A-R
  executed this correctly).
- CROSS-LANE RE-GRADE (governance 2026-08-30): any scorer/shared-file change that flips
  another lane's or program's committed state requires the AFFECTED lane's re-verification
  before the flip publishes.

READ ON EVERY REFRESH, IN THIS ORDER:
1. docs/handoffs/capx-director-ledger-2026-08.md — YOUR ledger. §0r (refresh #21 + its
   mid-sitting amendment) is the most recent entry; §1 lane scoreboard; §3 has all FIFTEEN
   owner rulings (Q5–Q15); §4 the prompt issuance record.
2. docs/handoffs/capx-director-prompt-pack-2026-08.md — every issued charter, landed ones
   annotated "historical record, do not re-run".
3. frontend/data/forecast/program-status.json + ff-verdicts.json — the gate board and LIVE
   verdicts. Read the BARE `<iso>-t1f/-t1x/-t1h` keys; suffixed keys (`-ff2d`, `-ffr3a2`,
   `-s4control`, `-pre-d5r`…) are PRESERVED baselines — quoting one as current is this
   program's most common historical defect.
4. frontend/data/backcast/keepers/<ISO>.json + calibration-complete.json + holdout-freeze.json.
5. docs/mechanism-testing-matrix.md + docs/codebase-site/data/mechanism-matrix/<ISO>.js.
6. The newest FINDINGs/PRECOMMITs in docs/handoffs/ and docs/ (ls -t both), newest first.

STATE AT HANDOFF (2026-08-31, refresh #21 + dispatch, main HEAD 49a3ac13) — VERIFY, DON'T
TRUST. If the r#21 dispatch commit is not yet on main, branch
claude/calibration-workstream-relaunch-bml7zm carries the latest ledger + pack.

IN FLIGHT (five lanes + one watched): NEISO-RC-R (repair phase R2+R1+R3+R4, Fable,
claude/capx-neiso-rc-repair) · D3 (MISO t1h retire.total_gw flip attribution, Fable,
claude/capx-d3-miso-retire-g3) · D4-I3 (ERCOT scarcity-slack half, Opus,
claude/capx-d4i3-ercot-slack; net-revenue half HELD under card Y-C) · D8-RE (deferred
verdict/board re-emission, Opus, claude/capx-d8-re-emission) · plus the owner's backcast
lane miso-193 (cc_duct_peaking, PREREG'd A/B, sections pending — watch only). D6 (FC-3
curve-ON over-fire) is HELD one batch, sequenced after D4-I3 (post-arming T1-H measurement
contention). On next refresh: grade all five, collision-map the next batch.

RECENT LANDINGS THAT SET CONTEXT: the T3 golden REGISTERED the first §2.1b full-horizon
campaign (PRs #4447/#4452, R-A posture-epoch caveat on its record) · S-6 measured PJM FC-1
FAIL = {I7, I12} (not I7 alone) · D12-A armed entry_margin_exhaustion +
entry_forward_reserve_leg as ERCOT forecast defaults (Q15) · T1-H storage-entry Leg A armed
(owner ruling R-A) · MISO keeper → 2026-08-30-miso-191-bexit (NOT-YET on {C3a-2025} alone) ·
ercot-245 killed at census (K-A/K-C/K-T; SCED conduct-corpus intake is the named unblock) ·
ercot-246 ruled ISO-level determination of a partitioned keeper = worst config over
designated spans — ERCOT reads CALIBRATED · caiso-226/227 landed the OFO + Helms
ps-water-state intakes, C3a-2025 root cause an honest null, the caiso-227 arm pre-registered
UNFUNDED · nyiso-163b owner ruling: AORR access route CLOSED permanently, a C3c SCARCITY
PROGRAM opens (the next NYISO lane is that program's first, unchartered).

KEEPERS/MARKERS SNAPSHOT (verify against the files): complete = {NEISO, PJM}; final EMPTY;
freeze tier-scoped to the locked test; frontier = {PJM, NEISO}; NYISO withdrawn (Q5-W),
keeper nyiso-159-loss-surface NOT-YET; CAISO caiso-220 NOT-YET at terminal rest (next dated
sweep ≤ 2026-12-01); ERCOT two-config keeper, reads CALIBRATED under ercot-246.

OWNER-TIER ITEMS OPEN (present as decision cards when the owner sits): (a) the nyiso-161
winter-face-waiver card; (b) chartering the nyiso-163b C3c scarcity program's first lane;
(c) miso-192's D-4 posture options (i)/(ii)/(iii); (d) caiso-227 arm funding; (e) the ERCOT
2024/2025 SCED conduct-corpus intake; (f) D6 release once D4-I3 lands.

POST-SNAPSHOT DELTA (landed while this handoff was being written — grade these at your first
refresh; everything above them still holds): **ercot-247: the owner DECLARED ERCOT complete +
frontier (2026-08-31, PR #4454) — the first ERCOT rule-22 marker**, so the marker/frontier
snapshot above is superseded: complete/frontier now include ERCOT (verify the
calibration-complete.json entry text and its Q5-uniform-rule footing on the ercot-246
partitioned-keeper CALIBRATED read). **D3 CONCLUDED** (PRs #4455/#4458: precommit + attribution
— the G3 fix unmasked a compensating error; MISO G3 board row refreshed). **D8-RE EXECUTED**
(PR #4457). **pjm-164** audited PJM's C3c reserve-dual channel for the ercot-214 phantom
signature — verdict REAL. In-flight set is therefore: NEISO-RC-R · D4-I3 · miso-193 (watch).

DUTIES ON EVERY DISPATCH: every prompt carries its DATA PROFILE line, model, branch stem,
binding charter citation (pack section or precommit), collision-care lines, and rules 22/27/28
reminders. Record every issuance in ledger §4 and the scoreboard in the same sitting; push
blob-verified (rule 27) — your ledger and pack are both ≥300-line files. One sitting = one
refresh entry (§0-series), amendments appended mid-sitting rather than rewritten.
```

---

## r#22 DELTA (2026-08-31, main HEAD `d44446e0`) — append, not a rewrite

Everything above still holds except where this section supersedes it. Full record: ledger §0s.

**GRADED AT r#22:** D3 **LANDED** (PRs #4455/#4458) · D4-I3 **LANDED** (PR #4460) · D8-RE
**LANDED** (PR #4457, and it STOPPED two verdict flips rather than publishing them) ·
**NEISO-RC-R NOT GRADED** — no branch, no commits, and under the relaunch protocol that is not
evidence of loss; the owner has been asked whether the session is still running. Nobody
launches a second one until the answer is in.

**MARKERS (superseding the snapshot above):** `complete` = **{ERCOT, NEISO, PJM}** (ercot-247,
PR #4454 — the first ERCOT rule-22 marker, resting on the ercot-246 partitioned-keeper ruling);
`final` still EMPTY; `withdrawn` = {NYISO, CAISO}; freeze still tier-scoped to the locked test.
ERCOT's forecast gate (a) now passes on the literal test — a board fact no lane has written yet
(queued as D19).

**IN FLIGHT after the r#22 dispatch:** D8-V (FC-7 ledger completion, Fable) · D4-M (ERCOT
post-arming T1-H + the R-4 instrument grain, Opus) · D17 (MISO's missing non-coal exit channel,
Fable) · D18 (invariant declaration ledger, Opus) · NEISO-RC-R (status unknown, see above).
**QUEUED:** D6 (still uncharted — and re-scoped: it is NOT the ERCOT measurement vehicle,
ERCOT is curve-OFF) · D19 (board reconcile 2, deliberately after D8-V + D4-M) · D20
(reconstructed-run_config provenance — director decision taken: adoption-as-original REFUSED,
the admissible route scores a `reconstruction` label CAVEAT, never PASS).

**OWNER-TIER ITEMS OPEN (replaces the list above):** (a) NEISO-RC-R — still running? · (b) the
T3 golden's R-A re-solve (a second §2.1b campaign, outside Q13's "this campaign only" scope;
material because the golden's headline result is ZERO storage entry in 25 years and R-A armed
exactly the storage-entry mechanisms) · (c) C3c program Q3, the probabilistic RT premium —
an architecture decision the charter recommends NOT opening · (d) the ERCOT 2024/2025 SCED
conduct-corpus intake · (e) the nyiso-161 winter-face waiver card, still unruled · (f)
miso-192's D-4 posture options. **CLOSED since r#21:** caiso-227 arm funding (funded; caiso-228
executed it and it died at gate D1) and chartering the C3c program's first lane (the charter
exists and Q1/Q2 are both spent — pjm-164 REAL, nyiso-164 confirms NYISO's ledger).

**r#22 AMENDMENT (same sitting).** **NEISO-RC-R LANDED IN FULL** (PR #4467) — my census missed
it because I searched by BRANCH STEM and the lane ran on `claude/neiso-rc-repair-fymtkz`.
Standing lesson: **grade by content (`git log origin/main --grep=<LANE-ID>` + merged PRs),
never by branch name.** Four owner rulings taken: **Q16** golden re-solve HOLD, fix the t3
ceiling first (FC-5/FC-6 are required at t3 and neither instrument exists for any ISO, so no
golden can grade better than HOLD) · **Q17** C3c Q3 NOT opened, so the C3c program CLOSES on
evidence · **Q18** the ERCOT SCED conduct-corpus intake FUNDED (offered as a backcast prompt) ·
**Q19** ceiling order = FC-6 then FC-5. Two more lanes issued: **D21** (FC-6 driver battery,
Fable) and **D22** (FC-5 `benchmark-corridor` datatype + intake, no scorer edit, Opus). Also
landed: the C3c audit (PR #4466) retracted its own Q2 false positive and found two defects in
`data/raw/_validation-source/actual_as_reserve_NYISO.parquet` — a nested reserve cascade must
be MAXED, never SUMMED, a rule now available to five other ISO lanes; and miso-194 (cold-snap
gas derate REFUTED, cell U→I). In flight after the amendment: D8-V · D4-M · D17 · D18 · D21 ·
D22.

**r#24 AMENDMENT (2026-09-01, main `1d280815`).** **The r#23 patch contingency is MOOT** — git
credentials returned, the held commit rebased/pushed and both files blob-verified. Ignore any
instruction above about `capx-director-r23.patch`. **THE t3 CEILING IS LIFTED** (D25: 78
dispositions, 0 UNEXPLAINED, FC-5 SKIPPED→CAVEAT on five keys; D21 had already made FC-6 grade),
so **owner ruling Q16's hold on the golden re-solve has expired on its own premise** and the
second-campaign question is live again — but decide it AFTER the FC-6 P1 instrument repair
(D26), since re-solving into an inverted P1 spends a campaign to re-measure a premise.
**RECORDED AGAINST INTEREST: the r#23 "a carbon price raises CO2, the model's economic core has
a sign error" alarm is REFUTED** (D23). The model's sign is right in both legs; a nonzero
`carbon_price` REPLACES the resolved signal and NEISO's base already carries the RGGI projection,
so the `carbon25` arm CUT the carbon price in every year. Do not carry the alarm forward.
In flight after r#24: D26 · D27 · D28, plus the owner's miso-196 and caiso-231.

**r#25 DELTA (2026-09-01, main `1658d8aa`) — append, not a rewrite. Full record: ledger §0v.**

**TWO DIRECTORS RAN ON ONE PROGRAM.** The r#23 container recovered its credentials, landed its
held ledger (PR #4503) and ran the r#24 sitting (PR #4505) — while the owner separately opened a
second director session from the stale r#23-era handoff. Grade-by-content caught it before any
collision. **STANDING PROTOCOL, now binding on every successor: on session open, compare your
handoff's newest-entry claim against the ledger's actual top §0-entry on main BEFORE grading
anything.** A handoff is a snapshot that can be a full generation stale; the ledger always wins;
re-derive your sitting number from the ledger's top entry and grade only the delta it missed.
The live director line is `claude/capx-director-refresh-0z0e0f` unless the owner says otherwise.

**GRADED AT r#25 (the delta r#24 could not see):** **nyiso-167 LANDED** (PR #4504) — NYISO's
C3a-2025 re-attributed to a YEAR-INVARIANT price-response gain (model = 0.703 × actual + $11.03,
R² 0.910, all 36 training months; C3a passes only for an annual actual mean inside
$27.8–56.0/MWh and 2025 is 19 % outside). The gain is CROSS-ISO: ERCOT 0.347 / MISO 0.500 /
PJM 0.668 / NYISO 0.703 / CAISO 0.837 / NEISO 0.986 — five of six keepers carry a bounded C3a
pass window in price level, NEISO is the in-repo proof it is closable, and MISO's
C3a-2025-only NOT-YET sits inside the same object. Measurement only — no verdict transfers
(rule 25). Carry it as a stated attribution limit on any price-level-sensitive forecast leg.
Also **PR #4485** (nyiso-165 verification + reference-side all-ISO cascade scan) discharged the
r#23 OWED item.

**FOUR OWNER RULINGS (Q20–Q23, ledger §3):** **Q20** cache-key repair = (c′)+(b′-1) zero-cost
pair, no retroactive re-key → lane D24-R (Opus) · **Q21** MISO D-4 posture = (iii) CONTINUE on
the named candidates (owner's backcast lane executes, miso-197+ after miso-196 lands) ·
**Q22** nyiso-161 winter-face waiver = OPTION A, no amendment — the card RETIRES
answered-by-measurement (its own eligibility test (a) measured NO); NOT-YET stands; no caveat
class created · **Q23** FC-5 external sources = **NONE FUNDED** ("I'm not getting more data") —
all five closed, FC-5's CAVEAT is the steady state, **DO NOT RE-PRESENT absent a new owner act.**

**IN FLIGHT after r#25:** D26 (FC-6 P1 arm repair, Fable) · D27 (MISO T1-H HEAD re-measure,
Opus) · D28 (long-position capacity revenue Phase-0, Fable) · **D24-R** (cache-key repair
execution, Opus, NEW) · **D29** (trajectory reporting grain, Opus, NEW) · plus the owner's
miso-196 (A/B arms pending) and caiso-231 (precommit filed) — watch only. **The D26/D27/D28
charters are now COMMITTED** (pack §D26/§D27/§D28, reconstructions labeled as such — r#24 had
issued them chat-only; relaunches restart from the pack). **QUEUED:** D6 (held behind
D27 + D28) · **D30 NEW-named**: the D25 §6.4 45Q conversion-pace question (held behind D27,
charter with D28's Phase-0 in hand) · D20 (decision taken, unchanged).

**OWNER-TIER OPEN (both deliberately not re-presented until D26 lands):** (a) the golden
re-solve / second §2.1b campaign — Q16's premise is discharged, and D25 §6.3 measured the
zero-storage-entry divergence as the corridor's largest cross-ISO family (−56 % to −96 %, four
ISOs — the R-A arms would move exactly those rows); decide AFTER the P1 instrument repair.
(b) whether neiso-t3's FC-6 FAIL survives D26's re-score — the affected lane's re-verification
decides publication. **CLOSED at r#25:** the D24 repair choice, the miso-192 posture, the
nyiso-161 card, and FC-5 source funding (Q20–Q23 — do not re-present any of them).

**r#26 DELTA (2026-09-01, main `8462da22`) — append, not a rewrite. Full record: ledger §0w.**

**THE NINE-WRITER WAVE: 7 landed, 2 clean checkpoints, 0 lost.** D24-R ✓ (cache-key defect
closed forward, zero keys moved) · D29 ✓ (trajectory grain in) · **D27 ✓ — the headline:
D17's 14.7 GW vindicated as arithmetic to the decimal, REFUTED as a remedy — the released
admission went 100 % to coal (+106.3 % over-retirement, G3 sign flips to +52.2 %), non-coal
exits still 0.000 GW; the SELECTOR is `_apply_reliability_floor`'s cheapest-firm-per-MW
retention key** (→ R5 = D32, queued) · **D28 ✓ — the $0-curve object decomposes into a
POSITION defect (model 6–22 reserve-ratio pts longer than real cleared positions; curves
themselves published-faithful) + a clearing-half question**; NYISO's curve-ON latent row is
D6's evidence · nyiso-168 ✓ (gain = ordinary-band slope deficit; market steepness NOT
physical; the one new mechanism LP-inert, killed ex ante) · caiso-231 **PROMOTED**
(keeper `2026-09-01-caiso-231-b1-ungrounded`, NOT-YET on C3a alone unchanged, nine
ERCOT-inherited multipliers retired) · stage-0 NEISO+ERCOT captures ✓ (audit R-L; both
oracles PASS) · **D26 = CHECKPOINT** (carbon_price_delta + exact golden control landed;
finding at TBD-HEADLINE with the owed-solves runbook) · miso-197 = CHECKPOINT (phase-0
census rule frozen). D30 owner-confirmed NOT DISPATCHED — pack §D30 stays live.

**AGAINST INTEREST — card duplication (§0w.2):** audit ruling **R-H had already ruled the
nyiso-161 card Option A** (recorded v18b D-7, before the r#25 card set); Q22 re-served it.
Same outcome, no divergence; primacy is R-H's. **New standing step: before serving ANY card,
grep the audit board's R-series ruling ledger for card-adjacent rulings.**

**RULED r#26: Q24 — the MISO PRA/RBDC intake is FUNDED** (tightly-scoped, S-123 document
class; owner fetches out-of-session, hands files to D31; **Q23 stands unchanged**).

**IN FLIGHT after r#26:** D26-S (the D26 runbook's solve half + FC-6 re-score, Opus) ·
D31 (MISO capacity-revenue repair — the PRIMARY lever, Q24-funded, Fable) · D33 (NEISO
position lane, informs the golden card, Fable) · D30 (issued, undispatched) · miso-197
(owner's, mid-lane). **QUEUED:** D32 (floor-retention monopoly, behind D31) · D6+D28-R3
(chartered JOINTLY after D31/D33 land — one mechanism-class charter, per-ISO parameters).
**OWNER-TIER:** the golden re-solve card, FC-6 survival, and D23's R4 carbon-semantics
question ALL wait on D26-S — present together when it lands.

**r#26 amendment-1 correction (same sitting, main `a40cfc68`):** the delta above is already
stale on three points. **D26 COMPLETED ITSELF** (PR #4522: P1 FAIL→PASS on the repaired arm,
neiso-t3 FC-6 FAIL→CAVEAT, HOLD unchanged) — **D26-S is RETIRED UNRUN**, and every item that
waited on it is discharged: **Q25 AUTHORIZED the second golden campaign** (T3-NEISO-GOLDEN-2,
issued, Fable) and **Q26 CLOSED R4** (replace semantics + below-base guard → D34, issued,
Opus). **D20 is RELEASED and issued** (its scorer-surface hold dissolved when D26+D27 landed).
miso-197 CONCLUDED (PR #4521, CC over-dispatch root-caused to the chronic gas-steamer/CHP
allocation defect; successor prereg frozen). In flight after amendment 1: **D31 · D33 · D30
(undispatched) · T3-NEISO-GOLDEN-2 · D34 · D20**. Transport note: a silent push hang with
reads flowing is the proxy's UPLOAD GATE, not transport death — one long-window (~9 m)
background push attempt after a fresh rebase is the remedy that worked (ledger §0w amendment
1, last paragraph).
