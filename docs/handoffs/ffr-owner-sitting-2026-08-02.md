# FFR owner sitting — decision packet (D-1 … D-7) — assembled 2026-08-02

**What this is.** The one-sitting owner-decision batch of
`docs/forecast-readiness-audit-2026-07.md` §4 Phase 2, assembled by session FFR-2D
(`docs/forecast-readiness-prompt-pack-2026-07.md` §Wave 2 — docs only: no code, no solve, no
dashboard registration, no default touched). Per item: what it changes, the evidence doc, what it
re-opens, a recommendation, and a sign-off line. **Nothing in this packet changes any default or
grants any authorization by itself** — every recommendation is decision-support; execution of a
signed decision is FFR-3A step 0 (config flips, one commit per decision, citing the signature)
and FFR-3B (governance-text edits). Decisions may also be explicitly **deferred**, which
re-scopes FFR-3A step 0 to the signed subset (pack §Wave 2 gate note).

**State basis — read at `origin/main` `a92ae97` (2026-08-02), re-verify at the sitting.** Every
keeper id, marker, and freeze state below was read from the governing file at this head, not
copied from a doc. Keepers move ~daily (~20 promotions in the 10 days before the audit — audit
FR-21); the sitting re-reads `frontend/data/backcast/keepers/<ISO>.json` at its own head before
relying on any id here.

- **Wave 1 is fully merged** (FFR-1A/1B/1C/1D/1E + PA/PB — all seven handoff docs in
  `docs/handoffs/`). **§W1-X is outstanding at this head**: no operator cache-epoch bump commit
  on `origin/main` yet, and FFR-1E's parity CI job is not yet in `ci.yml` (held for FFR-1D's
  file ownership; 1D merged as PR #3245). §W1-X must complete before FFR-3A's battery re-solves.
- **Keepers at this head:** ERCOT `2026-08-01-ercot149-gas-event-cap` · PJM
  `2026-07-31-pjm-143b-hy-level` · CAISO `2026-07-31-caiso-151-firm-selfsched` · NYISO
  `2026-08-01-nyiso109-zonal-margin-anchor` · NEISO `2026-07-31-neiso-72-hy-window` · MISO
  `2026-07-31-miso-109b-hy-level`.
- **Markers** (`frontend/data/backcast/calibration-complete.json`, two-block structure, owner
  decision 2026-07-31): `complete` = **{NEISO, NYISO, PJM}** — NEISO declared 2026-07-07,
  re-scoped validation-only 2026-07-31 (its locked test is **SPENT, never re-grantable**); NYISO
  re-declared 2026-07-31 (CALIBRATED-WITH-CAVEATS, C3c ledgered, at `nyiso-100`; the 2026-07-13
  withdrawal is superseded); PJM declared 2026-07-31 (CALIBRATED, zero caveats, at `pjm-140`).
  `final` = **deliberately empty** ("Neither is final").
- **HOLDOUT SPEND FREEZE ACTIVE** (`frontend/data/backcast/holdout-freeze.json`: declared
  2026-07-25, HELD 2026-07-26 under the charter's adopt-and-hold verdict; cause: the CAMPD
  economic-layup residual over-count that survives the merit-order guard). Nothing
  out-of-training is solvable/scorable/registrable for any ISO while it stands; the lift is the
  owner's alone and **outside this program**. Nothing in this packet spends, schedules, or
  depends on an out-of-training year; per pack §0a, the program's T1-F/T1-X/T1-H windows as
  specified and all in-sample 2023–2025 work are outside the freeze's scope.

**Evidence attachment status (assembly time).** The Wave-2 evidence sessions had not landed at
`a92ae97` — no `docs/handoffs/ffr-2*.md` exists yet. The sitting convenes when the attachments
land (pack §Wave 2 gate: "evidence docs committed → OWNER SITTING"):

| Evidence doc (expected path pattern) | Feeds | Status at assembly |
|---|---|---|
| `docs/handoffs/ffr-2b-<topic>-<date>.md` (+ registered probe runs) | **D-1, D-2** | pending |
| `docs/handoffs/ffr-2c-<topic>-<date>.md` (+ re-anchor commits) | **D-3** | pending |
| `docs/handoffs/ffr-2e-<topic>-<date>.md` (posture-divergence table) | context for **D-1/D-3** — a sloped-curve validation posture changes what those flips are judged against (pack §FFR-2E) | pending |
| `docs/handoffs/ffr-2a-<topic>-<date>.md` (input-gap table vs current keepers) | sitting context (worth-the-compute, §2.1b(c)) | pending |
| `docs/handoffs/ff-g2-fuel-forward-2026-07.md` | **D-4** | **landed** |
| `docs/handoffs/ff-g3-net-cone-forward-2026-07.md` | **D-3** owner box | **landed** |
| This packet §D-5/§D-6/§D-7 (no Wave-2 dependency) | **D-5, D-6, D-7** | **decidable now** |

---

## Addendum A — attachments landed after assembly (workstream manager, 2026-08-02, HEAD `d5d5b6f`)

*Appended by the FFR/FH workstream manager, not by FFR-2D. The body of this packet is left as
assembled; this section carries what moved since `a92ae97` and supersedes the assembly-time
"pending" rows above. Two of the items below change the evidence base a decision rests on, so
read this before signing D-1 or D-2.*

**A.1 §W1-X is no longer outstanding — Wave 1 is CLOSED.** The state-basis bullet above was
true at `a92ae97` and is now stale. §W1-X ran and reported **GREEN** (PR #3265,
`docs/handoffs/ffr-w1x-wave1-close-2026-08-02.md`): the three attestations pass, the single
operator cache epoch was taken 2026-08-02 (ledger in `src/market_sim/results/cache.py:47+` —
every pre-2026-08-02 **forecast-mode** cache invalid; backcast caches and all six keeper
bundles explicitly NOT), the three-part regression audit passes, and FFR-1E's
`forecast-parity-guard` job is in CI. FFR-3A's battery is therefore unblocked on this axis.

**A.2 D-1 / D-2 attachment has LANDED:** `docs/handoffs/ffr-2b-retirement-entry-evidence-2026-08-02.md`
(PR #3277). Its bottom line, relayed without re-litigation:

- **D-1 — the pre-registered bar is MET in both curve-ON ISOs.** T-R10a and T-R10b go
  FAIL→PASS holding **3/3** LOYO folds; recall FAIL→PASS (MISO 12 %→76 %, PJM 53 %→76 %);
  bands imported and never widened; no new invariant failure; additions **byte-identical**
  across arms. The zero-real-fuel inversions close completely (MISO `gas_st` 12.920→0.0 GW;
  PJM `gas_st` 10.358→0.0 and `gas_ct` 11.379→0.0). D-1's recommendation above was
  conditional — *"flip iff FFR-2B's post-W1 probes clear the T-R battery + T-R10 + LOYO with
  bands unchanged"* — and **that condition is now satisfied on its own terms.**
- **D-2 — arm, but sign knowing the bar is only PARTLY met.** The FR-13 precondition is
  confirmed fixed (**I4 stays PASS with the commissioning lag armed** — the latent-defect
  test). Against that: the rate limit **re-phases rather than reduces** cumulative backstop MW
  (−0.07 %), I13 had **no cobweb to remove**, and **I12 goes WARN→FAIL** — because the dampers
  stop concealing a shortfall the base arm was closing with an unbuildable 4.9 GW single-year
  CT wave. That is a disclosed adequacy change, not a regression to fix by unarming.
  `entry_vre_capacity_revenue` remains **unprobed** and separately signable.

**A.3 TWO findings that change D-1's evidence base — neither is in the body above.**

1. **Wave 1 made the shipped legacy rule substantially worse, with no rule change.** MISO
   false-retire 8.643 → **12.920 GW**; PJM 4.097 → **22.342 GW (5.5×)**. Consequence for this
   sitting: **the pre-W1 FF-1A numbers quoted in D-1's "Why it is in front of you" understate
   the case**, and they are not a valid baseline for judging the flip. The harm the flip
   avoids is larger than the packet body says.
2. **MISO legacy's thermal LEVEL band passed (−0 %) purely by cancellation** of two large
   opposite-signed composition errors. Reading that pass as the better result is precisely the
   rule-1 `[R-STRUCT]` failure mode — a right number reached through a wrong mechanism. It
   should not be counted in legacy's favour.

**A.4 D-1 is now on Wave FH's critical path.** FH-1 merged (PR #3269) and its §3.3
harness-defect gate **FAILED** — the I6 over-retirement reproduces at the T1-FF posture
(ERCOT base 2023: 21.05 GW = **26.8 %** of prior thermal retired in 2025; I6/I7 FAIL, I12
WARN), so **FH-4 / Phase A is BLOCKED** (pack §0d; plan §3.3 gate-result block). FFR-2B's §4
cross-read measures `pipeline` moving I6 **down** — PJM 12.68→8.55 % (**−33 % relative**),
MISO 9.06→8.37 % — and is explicit about the limits: neither ISO it could measure ever FAILS
I6 under either rule, so this **cannot** demonstrate the flip converting a failing case into a
passing one, and rule 25 `[R-ISO-SCOPE]` forbids assuming the effect transfers to ERCOT.
Critically, **the single-year lumping SURVIVES the rule change** even though `pipeline` removes
the consecutive-loss counters outright — which isolates **G-31 screen grain as an independent
root-cause term**, not a symptom of the decision rule. So the FH-4 unblock needs **D-1 plus a
G-31 lane fix plus a re-probe**; signing D-1 is necessary, is not sufficient, and does not by
itself lift the block.

**A.5 Attachments still pending:** ~~FFR-2C (**D-3** — not started as of this HEAD: no branch, no
PR, no handoff)~~ → **LANDED, see Addendum B; D-3 is now DECIDABLE.** Still pending: FFR-2E
(context for D-1/D-3), FFR-2A (sitting context). D-5, D-6 and D-7 remain decidable now, as
assembled.

**A.6 Keeper drift since assembly:** CAISO → `2026-07-31-caiso153-reid-b` (PR #3267). The other
five are unchanged from the state-basis list above. Re-read the shards at the sitting's own HEAD.

---

## Addendum B — FFR-2C landed; **D-3 is now decidable** (workstream manager, 2026-08-02, HEAD `cb1c416`)

Evidence doc: `docs/handoffs/ffr-2c-net-cone-currency-2026-08-02.md`; the owner box itself is
written into `ff-g3-net-cone-forward-2026-07.md` §5. **No default was flipped and no escalation
option was armed** — the shipped mode is still `hold_last` with every real rate at 0.0.

**B.1 The re-anchor (the half that was never yours).** Two of four stale vintages moved, each
from its published instrument; the other two were adjudicated rather than guessed:

| ISO | held → re-anchored ($/kW-yr) | step | = years of +2 %/yr real |
|---|---|--:|--:|
| **PJM** | 88.52 → **118.88** | **+34.3 %** | **14.9 yr** |
| **NYISO** | 50.55 → **57.70** | **+14.1 %** | **6.7 yr** |
| MISO | 79.80 held | +1.5 % derivable, **not taken** | 0.8 yr |
| NEISO | 108.94 held | no newer vintage exists | — |

**The framing this forces on D3-1/D3-2:** currency dominates escalation. A single PJM vintage
refresh is worth ~15 years of +2 %/yr real, and ~4 more PJM vintages plus ~24 NYISO annual
updates land inside the 2026–2050 horizon. **Keeping vintages current needs no owner decision at
all — it is maintenance.** Sign the escalation box knowing it is the smaller lever.

**B.2 A finding that SUPERSEDES a prior conclusion — read before D-3 or D-1.** PJM's new vintage
carries a **published price floor that removes the demand curve's zero-cross**. That supersedes
FF-2C's "the PJM curve flip is quantitatively inert" from **solve year 2028 onward**. Any D-3 or
D-1 reasoning resting on the PJM curve being inert is reasoning from a superseded premise. It
also raises the value of FFR-2E's still-pending posture-divergence table, which is exactly the
curve-ON-vs-fixed question.

**B.3 D3-3 (intake authorization) is largely MOOT — the premise was wrong.** FF-G3 filed all four
vintages as MANUAL DOWNLOADS NEEDED on a bot-wall diagnosis. Re-probed: the PJM Planning-Parameters
**XLSX returns HTTP 200** (39,244 bytes, a real workbook — every PJM number above comes from it),
and the NYISO parameters were simply linked from the Installed Capacity Market page rather than
the demand-curve page. Only MISO is a genuine block, and it is one object's ACL (**HTTP 403** on
the 2026 PRA posting while 2023/24/25 on the same CDN return 200) — not a host-level wall. The
session's own lesson, worth adopting program-wide: **re-probe a filed MANUAL-DOWNLOAD row before
treating it as blocked, and name the exact object that fails, not the host.**

**B.4 The measured D1/D2 spread** (2050 anchor, on each ISO's *re-anchored* base, using each
ISO's **published** gross−net offset — not an illustration): at r = 2 %, `reindex_gross` vs
`hold_last` is **+130 % (PJM)**, **+139 % (NYISO)**, **+102 % (MISO)**. NEISO's `reindex_gross`
cell is **n/a because no FCA-18 gross CONE is on disk** — do not fill it by inference.

**B.5 The recommendations, now evidenced rather than expected.**
- **D3-2 = 0.0 real central, CONFIRMED by the new data.** PJM's +34.3 % is a *step* PJM itself
  labels a new cost basis; fitting a real rate to it extrapolates a one-time re-basing across 23
  years — the exact error the 0.0-central finding exists to prevent. NYISO cuts the same way from
  the other side: most of its move is a **falling E&AS offset**, which no construction-cost index
  produces at all.
- **D3-1 is inert until D3-2 chooses a non-zero rate** (at r = 0.0 all three modes are
  byte-identical to `hold_last`). Option (a) `reindex_gross` is cheaper to adopt than in July —
  the published offsets are now on disk for three of four ISOs.
- **D3-5 gains a natural experiment that argues FOR the coupling** — PJM's step is a new-build
  capital-cost re-estimate propagating into the capacity anchor, which is what D5 proposes — **but
  the two ISOs decompose oppositely**, so if D5 is taken it must couple the **gross leg only** and
  leave E&AS as its own driver. That is also what `reindex_gross` does, making **D5 and D3-1(a)
  the same decision seen from two ends** — consider signing them together or not at all.

**B.6 Epoch debt, as the D-3 section anticipated.** The re-anchor is a constants-level change:
forecast output moves under unchanged `ScenarioConfig` cache keys, and it landed *after* §W1-X's
single bump. **FFR-3A must clear this debt before its consolidated battery** — it is now a
concrete item, not a hypothetical.

**B.7 What remains pending:** FFR-2E and FFR-2A. D-1, D-2, D-3, D-5, D-6 and D-7 are decidable
now; only D-4 was never gated on Wave 2.

---

## Addendum C — **THE SITTING WAS HELD; all eleven decisions are signed** (workstream manager, 2026-08-02, HEAD `b9a96a9`)

*Appended by the FFR/FH workstream manager, not by FFR-2D. The packet body below is left as
assembled. This section carries the owner's signatures, the one place where a decision's premise
was found WRONG and corrected before signing, what landed mid-sitting, and the new decisions that
landing surfaced. **Where this section and the body disagree, this section wins.***

### C.1 The signed set

| # | Decision | **SIGNED** | Note |
|---|---|---|---|
| D-1 | Retirement rule `legacy` → `pipeline` | **FLIP** | On FFR-2B's met bar. See C.4(c) — a caveat on that evidence surfaced after signature. |
| D-2 | `entry_rate_limits` + `entry_commissioning_lag` | **ARM BOTH** | Signed knowing the bar is only partly met and I12 goes WARN→FAIL as a *disclosed adequacy change*, not a regression to unarm. |
| D-2′ | `entry_vre_capacity_revenue` | **HOLD** | Until it has its own probe row. Separable, unprobed; explicitly not armed on a decomposition study. |
| D-3a | Net-CONE forward-evolution mode | **DEFER until FFR-2E lands** | **Condition DISCHARGED — see C.3.** Operationally inert at the signed 0.0 rate (all three modes byte-identical), so the defer cost nothing. Re-put to the owner. |
| D-3b | Forward real escalation rate | **0.0 REAL CENTRAL** | Confirmed by the re-anchor data from both directions (PJM step = one-time re-basing; NYISO move = falling E&AS offset). |
| D-3c | Vintage intake authorization | **AUTHORIZE** | Largely moot — the bot-wall premise was refuted on re-probe. Keeps open the channel FFR-2C measured as dominant. |
| D-3d | ISO-NE post-FCM regime | **DEFERRED (blocked)** | **Not put to the owner** — no live alternative exists (blocked until CAR-SA files, expected Q4 2026). Recorded per the packet's own proposal. One line formalizes it if wanted. |
| D-3e | Gross-CONE ↔ new-build coupling | **AUTHORIZE ANALYSIS ONLY** | Signed while D-3a is deferred; B.5 called them one decision from two ends. Coherent here — the analysis feeds the deferred mode choice rather than pre-empting it. |
| D-4 | Forward fuel path | **OPTION A** (status quo) | Re-opens nothing. |
| D-5(a) | §2.1b(a) gate amendment | **ADOPT the paragraph** | Gate (a) keys on `complete`; `final` never required for forecast work. Reads as met by NEISO/NYISO/PJM. FFR-3B executes verbatim. |
| D-5(b) | Marker keeper-snapshot policy | **OPTION B — RE-KEY on promotion** | **Against the packet's recommendation; the owner's call.** Implementation signed as **re-verify the determination on each promotion**, so the marker never asserts an unscored determination. Accepted cost: a verification pass at keeper cadence (~20 promotions/10 days). |
| D-5(c) | Stale tier-agnostic sentence | **FFR-3B CORRECTS IT** | A live governance file must not understate its own enforcement. |
| D-6 | FF-3D NYISO pair evidence | **SCHEDULE via FFR-3A** | Sequenced after D-1/D-2. **Sharpened by FFR-2E** — see C.4(b): the existing pair is a force-ON probe pair, not a shipped-vs-fixed pair. |
| D-7(i) | Golden fixture | **RE-ISSUE THE WAIVER, THEN MOVE IT OFF ERCOT** | **Neither option the packet offered.** See C.2. |
| D-7(ii) | Weather posture | **(a) single draw + weather-conditional label** | The peer review's minimum defensible posture. Applies to whatever golden exists after the D-7(i) move. |

### C.2 D-7(i) — the packet's premise was WRONG; it is corrected here, not in the body

The body's D-7(i) offers AUTHORIZE / HOLD and asserts "deadline pressure: the waiver expires
2026-10-31." The owner challenged the relevance; the manager verified rather than defended, and
**the challenge was correct on every count**:

1. **The 15-solve-year band check runs nowhere automatically.** `test_golden_bands_hold` is
   `@pytest.mark.slow` **and** `skipif` unless `RUN_GOLDEN_FORECAST=1`. The only `ci.yml`
   reference to `tests/golden/**` is a *path filter*, not a job that solves.
2. **What expires on 2026-10-31 is a no-LP test.**
   `test_golden_fixture_config_identity_is_current` hashes `ScenarioConfig(**REFERENCE_SCENARIO_KWARGS)`
   and compares to the seeded key. No LP is built. The consequence of expiry is a cheap test going
   red, not a blocked pipeline. **The body's framing overstated it.**
3. **The AUTHORIZE/HOLD binary was false.** `staleness_waiver.json`'s own `on_expiry` field names a
   third resolution the packet did not offer: *"or by re-issuing the waiver with a new expiry and a
   recorded owner decision."*
4. **ERCOT is the least-settled anchor of the six.** Keeper `ercot149` (now `ercot150b`) read
   `DETERMINATION: NOT-YET`, fail set {C3a, C3b, C3c, C7}, and ERCOT is **absent from the `complete`
   marker block** while NEISO/NYISO/PJM are in it. Pinning the regression fixture to the lane with
   open gate failures and near-daily keeper churn is a large part of *why* it keeps going stale.
   (CLAUDE.md's "the calibrated reference" means most-developed lane, not marker-holding.)

One count where the challenge did **not** hold, recorded for honesty: the fixture already sets
`use_campd_bins=False` explicitly to "bound runtime," so it is **not** running ERCOT's 1,458-generator
plant-level config. **The speed case for switching is weak; the calibration case is the strong one.**

**Signed:** re-issue the waiver with a new expiry and the recorded decision (cheap, no solve,
sanctioned by the waiver file) → **FFR-3B**. Then scope moving the fixture off ERCOT, NEISO named as
the target (holds a `complete` marker; cheapest measured lane, ~4.0–4.2 GB peak vs ERCOT plant-level
5.9 GB). **Open, and NOT covered by this signature:** seeding a golden on any ISO is still a
15-solve-year invocation over the §2.1b 5-year cap, and `golden_forecast_bands.py`'s schedulability
guard **will refuse without its own written authorization**. `iso="ERCOT"` is hardcoded in
`REFERENCE_SCENARIO_KWARGS` and both golden filenames are hardcoded, so the move is a code change,
not a flag. **The move needs its own scoped session and its own signed seed authorization.**

### C.3 FFR-2E LANDED MID-SITTING — D-3a's defer condition is discharged

`docs/handoffs/ffr-2e-shipped-capacity-posture-2026-08-02.md` (base `a900c67`) merged **while the
sitting was in progress**, unannounced; the manager found it on a routine refresh. D-3a was deferred
*"until FFR-2E lands."* **It has landed — the condition is spent and D-3a is decidable now.**

Its headline, relayed without re-litigation: for **PJM, NEISO and MISO the two arms are not a
perturbation of each other** — at the model's own reserve position the shipped curve arm pays **ZERO**
capacity revenue across 2021–2025 where the fixed arm pays full net-CONE, so the T1-H "curve-ON
over-fire" FC-3 FAILs are the **direct arithmetic consequence** of removing $77–109k/firm-MW-yr from
the retirement screen. **CAISO's curve-ON is provably inert** (no published CAISO demand curve in the
registry — proved, not asserted). **PJM's FFR-2C floor reverses the sign of the posture gap from
2028**: $0 → $63,875/firm-MW-yr, from 100 % below the fixed arm to 17.5 % below.

### C.4 New items FFR-2E surfaced — two are NEW OWNER DECISIONS, one is a caveat on a signed decision

FFR-2E explicitly routed these to the owner batch at FFR-3A step 0 (rule 24 — it changed no default):

- **(a) B1/B2 — two contradictory answers to "the posture we ship" exist in the tree.**
  `run_full_horizon.py::reference_config()` pins `cmc_by_iso = None` unless `--golden-posture` is
  passed, so a T0 or T1-F leg launched with no flag prices adequacy on the flat stub while
  production clears the curve — the same FR-14 shape, in the T0/T1-F runner. And `GOLDEN_CMC_BY_ISO`
  = {PJM, MISO, NYISO, NEISO, CAISO} vs shipped {PJM, MISO, CAISO, NEISO} — **they disagree on
  NYISO.** 2E calls B1 "a default-posture decision, not an oversight." **New owner decision.**
- **(b) NYISO's T1 gate cites the WRONG ARM.** `ff-t1-gate` §4.1 lists `nyiso-2021-2025-curve`, but
  production ships NYISO **curve-OFF**; that leg is a force-ON probe. Its shipped-posture twin is
  already committed. **Both still FAIL, so no determination flips** — only the number and the claim
  it supports. This sharpens signed **D-6**: the pair FFR-3A regenerates is a force-ON probe pair,
  not a shipped-vs-fixed pair. Separately: **every FC-3 citation in §4.1 is a pre-cache-epoch leg**
  and the epoch invalidates all of them — not a bookkeeping refresh (PJM moved 18.157 → 29.373 GW on
  a cold re-solve with *no* posture or rule change).
- **(c) A DISCLOSED CAVEAT ON D-1's EVIDENCE, surfaced after signature.** `correlated_forced_outage`
  and `entry_lookahead_reprice` ship `True` in production but the hindcast harness passes its own
  `False` over them. 2E states plainly that **FFR-2B's D-1 retirement-rule evidence carries the same
  caveat** (it ran with both pinned off). 2E's *own* arms are unconfounded (both pin identically).
  **This does not overturn D-1** — the T-R battery, recall and 3/3 LOYO folds stand — but the owner
  signed D-1 before this was visible, and it is recorded here rather than left in a lane doc.
  Un-pinning those two fields is itself a harness-default decision of the B1 class. **New owner
  decision.**
- **(d) B4 — CAISO cannot be FC-3 scored at all** (no `capacity_actuals_caiso.csv`). Costs nothing
  today because CAISO's posture divergence is provably zero, but any future CAISO capacity evidence
  needs the actuals built first.

### C.5 Scope consequences

- **FFR-3B (dispatchable now, no solves):** D-5(a) paragraph verbatim · D-5(b) re-key **with
  per-promotion determination re-verification** (the existing `calibration-keeper-auditor`, which
  already fires on promotion, is the natural home — implementation pointer, not a decision) ·
  D-5(c) sentence correction · **D-7(i) waiver re-issue with a new expiry citing this signature.**
- **FFR-3A step 0:** D-1 flip · D-2 arm both · D-6 NYISO pair regeneration (per C.4(b)) · the
  C.4(a)/(c) posture decisions **if signed**. Does **not** touch net-CONE evolution mode (D-3a) unless
  re-signed. Must still clear FFR-2C's constants-level epoch debt (B.6) before its battery.
- **Not authorized by anything here:** the golden reseed invocation (C.2), and any `final`-tier
  holdout spend — the freeze is untouched and its lift remains a separate owner act.

### C.6 State at signature

HEAD `b9a96a9`. Keepers: ERCOT **`2026-08-02-ercot150b-zonal-anchor`** (moved twice during the
sitting) · PJM `2026-07-31-pjm-143b-hy-level` · CAISO `2026-07-31-caiso153-reid-b` · NYISO
`2026-08-01-nyiso109-zonal-margin-anchor` · NEISO `2026-07-31-neiso-72-hy-window` · MISO
`2026-07-31-miso-109b-hy-level`. Markers unchanged (`complete` = {NEISO, NYISO, PJM}, `final` empty).
**Holdout freeze ACTIVE and untouched.** Wave 2 closes when **FFR-2A** lands — the last open lane.

---

## Addendum E — **FFR-SB's nuclear box is SIGNED; the licence ceiling is DECLINED by owner decision** (workstream manager, 2026-08-03, HEAD `bfeddc6`)

*Appended by the FFR/FH workstream manager. Records the owner's answers to FFR-SB's DB-A…DB-E
box, and the FFR-3C attribution that landed in the same window. **The DB-A answer declines the
memo's primary recommendation** — that is an owner decision, taken twice, and it is recorded here
as a deliberate simplification, not an oversight.*

### E.1 The signed set

| Item | **SIGNED** | Status |
|---|---|---|
| **DB-A** — primary design | **IGNORE LICENCE EXPIRATIONS ENTIRELY.** A reactor runs as long as it is economic. The registry feeds nothing in the exit path. | **Declines memo candidate (c).** Owner words: *"Ignore license expirations and assume the plants can continue running so long as its economic."* Re-put once with the measured consequence below and **REAFFIRMED**. |
| **DB-B** — SLR/renewal base case | **ASSUME RENEWAL** | **Signed but INERT** — with no ceiling to extend, there is nothing for the renewal assumption to act on. Recorded so a later reader does not mistake its inertness for an omission. |
| **DB-C** — non-renewal vocabulary | **REUSE the existing `regulatory_order` class** | **LIVE, and now load-bearing.** See E.3. |
| **DB-D** — sequencing and arming | **CONFIRM the ordering** | **Largely MOOT** for licence ceilings (nothing to implement or arm). Retains meaning only for the DB-C channel. |
| **DB-E** — chartering | — | **NO implementing session is chartered** for licence-ceiling consumption. `data/nuclear_license.py` and the 59-unit registry remain a curated data asset consumed by nothing in the solve path. |

### E.2 The measured consequence of DB-A, for the standing disclosure list

Put to the owner before the reaffirmation, computed from
`data/raw/nuclear-license-status/*.csv` (59 units):

- Only **11 of 59** reactors hold a *granted* subsequent licence renewal; **47 units / 51.2 GW**
  have a current licence expiring inside the 2026–2050 horizon without one.
- **Today the decision is nearly inert**: there are **zero** units that have declined to renew, so
  a ceiling would bind on nothing now. DB-A and the memo's candidate (c) are observationally
  identical across most of the horizon.
- They diverge for exactly **7 units / 6.04 GW, all in 2046–2050**: Perry 1 (2046), Clinton 1
  (2047), Nine Mile Point 1 (2049), Ginna 1 (2049), **Dresden 2 (2049)**, **Monticello 1 (2050)**,
  **Point Beach 1 (2050)**.
- **Three of those seven — Dresden 2, Monticello 1, Point Beach 1, 2.34 GW — hold an NRC-*granted*
  80-year endpoint**, and no regulatory pathway past 80 years currently exists. Under DB-A the
  model may dispatch them beyond the date their licence ends.

**This is a deliberate, owner-stated simplification.** It carries a rule 14 `[R-ACCURATE]` tension
— the licence dates are accurate measured data with a clean forward analogue — and the owner's
stated basis is that a plant should run so long as it is economic. **Any forecast quoting
post-2046 nuclear capacity in PJM, MISO or NYISO carries this assumption**, so it belongs in the
peer-review §4 standing disclosure list, not only in this packet.

### E.3 What still removes a reactor, under DB-A

DB-A removes the *paper-date* channel only. A nuclear unit can still exit exogenously through
**step 0 confirmed exits** when a licensee files permanent cessation (10 CFR 50.82) or withdraws a
renewal with a shutdown date — entered under the existing `regulatory_order` class per DB-C. That
is now the **only** exogenous nuclear exit channel, which raises DB-C from a schema footnote to
the load-bearing path. Economic retirement (step 3) is otherwise the sole determinant, as signed.

### E.4 FFR-3C landed in the same window — blocker 0 is ANSWERED

`docs/handoffs/ffr-3c-collapse-attribution-2026-08-03.md` (PR #3360). Nothing was tuned, unarmed,
widened, promoted or registered; both signed mechanisms stay armed. Its answer to the owner's
question is **(c) — both, with a measured split, and the split is MEMBERSHIP vs CALENDAR**:

- **WHICH units retire = REAL going-forward economics.** The corrected rule identifies them better
  than the rule it replaced (recall MISO 2/17→13/17, PJM 9/17→13/17, T-R10a/b FAIL→PASS on 3/3 LOYO).
- **WHEN they leave = GRAIN ARTIFACT.** The R-NEW redesign replaced a mechanism that had *both* a
  latency term and a throughput cap with one that has **only** the latency term, on the rule-19
  argument that queue latency and queue throughput are the same quantity. They are not: with only
  latency, **exit-wave width is invariant at exactly one year no matter how many units fail.**
- **The trough DEPTH is the INTERACTION — an asymmetry nobody measured before arming both halves:**
  **exit throughput uncapped, entry throughput capped at 2× the measured record** by D-2. Model
  single-year exits run **1.6×–4.8× the largest single-year thermal deactivation these ISOs have
  ever recorded**. The reserve-margin trough is the integral of that asymmetry.
- **MISO did NOT reproduce the ERCOT pattern and its I12 did NOT flip** — contradicting the
  sitting's own by-name prediction. MISO has **zero economic exits in the window**, so the second
  attribution the owner commissioned returns **no information about the retirement half**. **ERCOT
  remains the only ISO where D-1 is attributed at all**, and rule 25 `[R-ISO-SCOPE]` forbids
  importing it.
- **Instrument defect (§2.1): ERCOT's I12 band is on a different basis from the floor the model
  enforces** — a **6.65 pp** gap. FFR-3A's ERCOT headline is **overstated in magnitude**: the
  deepest excursion is **−8.65 pp, not −15.3 pp**, and it breaches in **three** years, not four.
  **The I12 FAIL verdict is robust and does not go away.** **CAISO's −3.1 % is NOT a basis
  artifact** — scored on the model's own basis, an 18.1 pp shortfall within the model.

**The new owner question this raises** (not signed, not put): whether to charter a G-31 fix lane
arming an **exit-throughput** mechanism to restore the symmetry D-2 broke. FFR-3C explicitly did
**not** ship one — the charter forbade it — and states that quantifying the artifact's share of
the ERCOT/CAISO trough *requires* one. §6 of its doc carries what such a lane would need.

---

## Addendum D — **Post-execution sitting: the four items FFR-3A raised are SIGNED** (workstream manager, 2026-08-03, HEAD `195ff18`)

*Appended by the FFR/FH workstream manager. Addendum C recorded the eleven decisions of the
2026-08-02 sitting. Executing them surfaced four more that nobody had authority over; the owner
signed all four on 2026-08-03. **Where this section and anything earlier disagree, this wins.***

### D.1 The signed set

| Item | Origin | **SIGNED** |
|---|---|---|
| **Adequacy collapse response** | FFR-3A §6.4 / §8 blocker 0 | **HOLD PROMOTION, FIND ROOT CAUSE** — keep D-1 and D-2 armed, promote nothing on these legs, dispatch the MISO control arm and the G-31 screen-grain investigation. |
| **C.4(c) harness pins** | FFR-2E §6.2, confirmed FFR-3A | **UN-PIN — MATCH PRODUCTION.** `correlated_forced_outage` and `entry_lookahead_reprice` stop being forced `False` against production `True`. |
| **C.4(a) B1 posture source** | FFR-2E B1/B2, FFR-3A §4.3 | **SINGLE SOURCE OF TRUTH.** Runners read the shipped `ScenarioConfig` field; the parallel `GOLDEN_CMC_BY_ISO` constant stops being a second answer. NYISO resolves curve-OFF, matching production. |
| **D-3a net-CONE evolution mode** | deferred at the 2026-08-02 sitting, condition discharged when FFR-2E landed | **(a) `reindex_gross`** — escalate gross by the published index, re-net the model's own simulated E&AS margin. **Byte-identical to `hold_last` at the signed 0.0 real rate**, so it changes no output until a non-zero rate is ever set. |

### D.2 The collapse decision, stated so no session mistakes it for a revert

The owner did **not** revert, un-arm, or widen anything. Both signed mechanisms **stay armed**.
What is withheld is **promotion**, and what is commissioned is **attribution**:

- **The MISO control arm** is the highest-value second attribution because the 2026-08-02 sitting
  predicted MISO's I12 flip **by name** — so MISO is the one ISO where a control tests a
  pre-registered expectation rather than fishing.
- **G-31 screen grain** was already isolated as an **independent root-cause term** in Addendum
  A.4: the single-year lumping **survives** the rule change even though `pipeline` removes the
  consecutive-loss counters outright. It was a live suspect before the collapse was measured.

A session that responds to this by reverting a default, unarming a damper, widening a band, or
tuning a parameter has misread it — that is precisely the rule 1 / rule 14 failure FFR-3A
avoided. **The deliverable is attribution, not a smaller number.**

### D.3 What the un-pin costs, acknowledged at signature

Un-pinning changes what every **committed T1-H verdict** means. Those verdicts become **legacy
evidence scored on a superseded posture** — they are not silently reinterpreted and not deleted.
Any FC-3 citation resting on them says so. This is the same "validate the configuration you
ship" principle that justified FFR-2E's lane (audit FR-14); the cost was known when signed.

### D.4 Still open after this addendum

- **FFR-SB's nuclear-registry owner box** (4 sub-decisions; the memo recommends candidate (c),
  grades (a) NON-VIABLE, (b) narrow-instrument-only). Not put to the owner yet.
- **FFR-3A blocker 4** — the optional-field cache-key hazard *"will silently recur on the next
  default flip; structural, needs a decision not a patch."* D-3a's mode flip is the next default
  flip, so this is now live rather than hypothetical.
- **FFR-3A blockers 1, 5, 6, 7, 8** — `data/clean` prerequisite (≈55 min/1.6 GB, undocumented),
  the T1-F console line reporting `0 FAIL, 0 WARN` on a zero-year run, 24 pre-existing test
  failures on main, `run_full_horizon.py` never writing `run_config.json` (so **FC-7 fails on
  every T1-F leg by construction**), and FC-2 row4 SKIPPED everywhere (so **BLK-10 backstop
  sizing, which D-2 was meant to re-open, cannot be scored at all**).
- **The battery is half-run.** No T1-H re-scores, no T1-X fold, no FC-6 driver battery, no FF-3E
  re-run, no §2.1b gate scorecard, no regression table vs FF-2D, no board regeneration, no
  registration. Every leg scored so far is **HOLD**.

### D.5 State at signature

HEAD `195ff18`. Keepers: ERCOT `2026-08-02-ercot150b-zonal-anchor` · **PJM
`2026-08-03-pjm-147b-chp-heat` (CALIBRATED 9/9)** · CAISO `2026-08-03-caiso156-meter-screen-b` ·
NYISO `2026-08-02-nyiso-113-li-locational` · NEISO `2026-08-03-neiso-caiso156-meter-screen` ·
MISO `2026-08-03-miso-117b-ct-heat`. Markers unchanged (`complete` = {NEISO, NYISO, PJM},
`final` empty). **Holdout freeze ACTIVE and untouched.**

---

## D-1 — Retirement-rule default: `legacy` → `pipeline`

**What it changes.** `ScenarioConfig.retirement_rule` default `"legacy"` → `"pipeline"`
(`src/market_sim/config/scenarios.py:1180`; cache-key-registered at non-default, so the flip
moves forecast cache keys by construction — no silent reuse). The legacy rule is per-fuel
consecutive-loss counters (`retirement_years_*`); the pipeline rule is the implemented FF-1A
redesign (owner D1 = Option B, 2026-07-17, `ff-retirement-rule-redesign-2026-07.md` §3.6/§6):
one-screen decision at the unchanged `net_revenue < going_forward_cost` bar, joint
adequacy-capped cross-fuel pipeline entry, soft annual re-confirmation latch, and measured
per-fuel execution lags (EIA-860 announced-to-deactivation medians, rule-23-identified —
`retirement-dof-identification-2026-07-15.md`).

**Why it is in front of you** (audit FR-4). Every default forecast still executes the refuted
legacy rule — the exact configuration measured to eliminate PJM's coal wave (recall 76 % → 0)
and false-retire 8.6 GW of MISO `gas_st`; the T1-H FC-3 curve-ON over-fire FAILs (all four curve
legs) are its live signature (`ff-t1-gate-2026-07.md` §4.1). The peer review places the legacy
counter outside commercial practice entirely (no analogue in IPM/ReEDS/PLEXOS-LT, which screen
going-forward NPV / lifetimes+margin / integer NPV — peer review §3.1).

**Evidence doc.** ~~FFR-2B (pending)~~ → **LANDED 2026-08-02**:
`docs/handoffs/ffr-2b-retirement-entry-evidence-2026-08-02.md` (PR #3277) — pipeline-armed probe
arms at post-W1 HEAD, PJM + MISO curve-ON T1-H legs, scored on the T-R battery + T-R10
no-inversion + LOYO within 2023–2025, bands never restated looser. **The conditional
recommendation below is satisfied; see Addendum A.2.** Note also **A.3**: the pre-W1 FF-1A
figures cited in the paragraph above are now known to UNDERSTATE the legacy rule's harm
(Wave 1 worsened it — PJM false-retire 5.5×), so do not treat them as the baseline.

**What it re-opens.** Every T1-H FC-3 verdict (a flipped rule re-solves all four curve legs —
FFR-3A step 1); the FF-3D NYISO pair evidence should be regenerated only **after** this decision
(see D-6). No epoch debt from the flip itself (field is key-registered).

**Recommendation** (the audit's own D-1 framing, relayed): flip **iff** FFR-2B's post-W1 probes
clear the T-R battery + T-R10 + LOYO with bands unchanged — flip on evidence, not on the memo.

**Sign-off:** ☐ FLIP (evidence green) ☐ HOLD (state why) ☐ DEFER — owner: ________ date: ____

---

## D-2 — Arm the entry dampers (`entry_rate_limits`, `entry_commissioning_lag`; separable: `entry_vre_capacity_revenue`)

**What it changes.** Three default-off, cache-key-registered FF-2A gates
(`scenarios.py:2146,2163,2133`):

- `entry_rate_limits` → annual economic-entry builds and the reserve-margin backstop capped at
  `ENTRY_GROWTH_LIMIT_MULTIPLE` (2.0 — the ReEDS growth-constraint hard bound, NREL ReEDS
  documentation) × the tech's prior maximum annual install.
- `entry_commissioning_lag` → builds decide in year Y, commission at
  Y + `ENTRY_COD_LAG_YEARS[tech]` (LBNL "Queued Up" 2024: median IA→COD ≈ 25 months,
  2016–2023 builds); pending MW netted against queue caps.
- `entry_vre_capacity_revenue` (separable) → wind/solar entry candidates earn the
  ELCC-accredited RA payment through the same seam thermal entry uses (one adequacy resolver,
  rule 19; no-op in energy-only ERCOT). The BLK-8 decomposition measured the withheld payment at
  ~$8–11k/MW-yr, pivotal in PJM 2023 (`blk8-solar-entry-decomposition` 2026-07-15 §4).

**Why it is in front of you** (audit FR-5). Entry is bang-bang — margin > 0 builds the entire
remaining queue cap, ≤ 0 builds zero (`new_entry.py:1038-1039,1137`); the backstop fires the full
deficit in one step unless rate-limited (`adequacy.py:344-351`). MISO's I13 cobweb FC-2 FAIL is
the detector for exactly this alternation. FF-2A's probe measured the first-wave build
2.5 → 1.103 GW with dampers armed — a probe-arm measurement, not shipped behavior. The
precondition is landed: FR-13 (commissioned pipeline units invisible to I4 when the lag is
armed) was fixed by FFR-1A (2026-07-31).

**Evidence doc.** ~~FFR-2B (pending)~~ → **LANDED 2026-08-02**:
`docs/handoffs/ffr-2b-retirement-entry-evidence-2026-08-02.md` (PR #3277) — MISO T1-F with
pipeline + both dampers armed. **I4 stays PASS with the lag armed** (the FR-13 regression check
passes). I13 and BLK-10 re-measured. **The bar is only PARTLY met — read Addendum A.2 before
signing:** the rate limit re-phases rather than reduces backstop MW (−0.07 %), I13 had no cobweb
to remove, and I12 goes WARN→FAIL as a disclosed adequacy change.

**What it re-opens.** FC-2 (I13) verdicts and the BLK-10 backstop-sizing record; nothing else
expected — all three are identified constructions (published/measured parameters, no free knob).
Probes run jointly with D-1 in FFR-2B, so the two decisions share one evidence base.

**Recommendation:** arm the two dampers **iff** FFR-2B shows I4 green with the lag armed and
I13/BLK-10 improved without new invariant failures. Decide `entry_vre_capacity_revenue` on its
own probe row — it changes entry economics (BLK-7 term c), not entry dynamics, and can be signed
independently.

**Sign-off (dampers):** ☐ ARM ☐ HOLD ☐ DEFER — owner: ________ date: ____
**Sign-off (VRE capacity revenue):** ☐ ARM ☐ HOLD ☐ DEFER — owner: ________ date: ____

---

## D-3 — Net-CONE currency (FF-G3 box D1–D5)

**Two halves — only one is yours.** The **re-anchor itself is not an owner decision**: FFR-2C
executes it as a rule-23 data-change re-derivation, one commit per ISO, each citing the published
instrument (PJM 2028/29 BRA clearing **325.69 $/MW-day** vs the on-disk last vintage 2027/28
**242.52** — the +34 % staleness audit FR-19 flags; NYISO/MISO frozen at 2025-26 vintages;
re-anchors wherever a newer published vintage exists). The **owner half** is the FF-G3
owner-decision box (`ff-g3-net-cone-forward-2026-07.md` §5), which FFR-2C populates with the
measured spread each option implies vs hold-last:

- **D3-1 — forward-evolution mode** (recommended posture, still opt-in): (a) `reindex_gross` —
  FF-G3's recommendation: field-standard, escalate gross by the ISO index, re-net the model's own
  simulated E&AS margin; (b) `reindex_net` — sensitivity only; (c) `hold_last` — status quo,
  acceptable only if re-anchoring keeps the last vintage current.
- **D3-2 — forward real escalation rate**: confirm central **0.0 real** (inflation-only, cited),
  positive real rates only as labelled tightness sensitivities.
- **D3-3 — re-anchoring intake authorization**: the manual-download vintages FFR-2C cannot fetch
  (bot-walled hosts — FF-G3 lists PJM 2028/29, NYISO 2026/27, MISO PY26/27, ISO-NE
  FCA19-or-successor). Priority: PJM 2028/29.
- **D3-4 — ISO-NE post-FCM regime**: blocked until CAR-SA files (expected Q4 2026) — the packet
  proposes explicit deferral, not a decision.
- **D3-5 — gross-CONE ↔ new-build cost coupling**: analysis-only authorization (in-scope to
  analyze, out-of-scope to wire — FF-G3 §5).

**Evidence doc.** FFR-2C (pending) + the landed FF-G3 design doc. FFR-2E's posture-divergence
table is context: FC-3 evidence today is scored on fixed net-CONE pricing while production ships
curve-ON for PJM/MISO/CAISO/NEISO (audit FR-14), so the arm the evidence cites affects how these
choices read.

**What it re-opens.** Capacity-price formation in every capacity-market ISO's forecast; FC-3
comparisons re-scored at FFR-3A. **Epoch note:** the re-anchor is a constants-level change —
forecast output moves under unchanged `ScenarioConfig` cache keys, so it rides the operator
cache-epoch discipline (`results/cache.py`); a Wave-2 constants commit landing after §W1-X's
single bump adds epoch debt for FFR-3A to clear before its battery.

**Recommendation** (relaying FF-G3): D3-1 = (a) `reindex_gross`; D3-2 = 0.0 central; D3-3 =
authorize, PJM first; D3-4 = defer until CAR-SA files; D3-5 = authorize analysis only. All
conditional on FFR-2C's measured spreads landing as expected.

**Sign-off D3-1 (mode):** ☐ (a) reindex_gross ☐ (b) ☐ (c) — owner: ________ date: ____
**Sign-off D3-2 (rate):** ☐ 0.0 central ☐ other cited basis: ________
**Sign-off D3-3 (intake):** ☐ AUTHORIZE ☐ HOLD **D3-4:** ☐ DEFER (blocked) **D3-5:** ☐ analysis-only

---

## D-4 — Forward fuel path: Option A vs B (FF-G2 §6, standing box)

**What it changes.** Nothing on Option A. The forward gas basis is already the AEO2026 refresh;
**Option A (pure AEO2026 annual paths)** is the status quo shape. **Option B** adds a formulaic
near-term STEO/NYMEX-strip blend decaying into AEO over 12–24 months.

**The measured case** (`ff-g2-fuel-forward-2026-07.md` §6): the AEO2026 vintage bump alone closed
the near-term gap to **+$0.2 vs STEO** (was −$0.9), so the blend is now low-value: rule-13
admissible if formulaic, but it moves the near term only ~$0.2 (downward) while adding a
maintained second source, a test, and a probe. Benchmarks/strips are context, never fit targets,
under either pick.

**Evidence doc.** Landed (FF-G2 §6). No Wave-2 dependency.

**What it re-opens.** A = nothing. B = the near-term fuel path in every ISO + the new blend
machinery's maintenance surface.

**Recommendation** (relaying FF-G2): **Option A.**

**Sign-off:** ☐ OPTION A ☐ OPTION B ☐ DEFER — owner: ________ date: ____

---

## D-5 residue — marker governance (the declarations themselves are DONE)

The audit's original D-5 (PJM marker declaration + NEISO re-key briefs) is **overtaken by your
own 2026-07-31 acts**: PJM declared, NYISO re-declared, NEISO re-scoped, all in the two-block
restructure. No calibration-complete memo is owed or written. Three residue items remain:

### D-5(a) — §2.1b(a) reconciliation amendment (sign here, FFR-3B executes)

The plan's gate-(a) text (`docs/forecast-development-plan-2026-07.md` §2.1b(2)(a)) predates the
complete/final split: it requires "the ISO's calibration-complete marker present" and cites the
**superseded** NYISO withdrawal as its example. Proposed one-paragraph replacement for owner
sign-off (executed verbatim by FFR-3B, per pack §FFR-3B step 3):

> **(a) Backcast calibration proof.** The ISO's backcast calibration is complete: a designated
> full-span keeper (rule 16) on the calibration dashboard AND an entry for the ISO in the
> **`complete` block** of `frontend/data/backcast/calibration-complete.json` (the validation-tier
> block of the two-block marker structure, owner decision 2026-07-31 — the same object rule 22
> keys on). The **`final`** (locked-test) block is **never required for forecast work**:
> locked-test years are backcast holdout instruments, and no forecast instrument reads them. A
> withdrawn or never-declared `complete` entry closes this gate until the owner (re-)declares.
> The holdout spend freeze is orthogonal: it suspends out-of-training solves, not the marker's
> role as calibration attestation, so an active freeze does not by itself close gate (a). The
> model first proves it can reproduce reality where reality is known.

Consequence once signed: gate (a) reads as **met by three ISOs at this head** (NEISO, NYISO,
PJM), matching pack §0a's "arguably met by THREE ISOs" — the other §2.1b conditions (b)–(d)
still gate every full solve, and the freeze still gates every holdout spend.

**Sign-off:** ☐ ADOPT the paragraph ☐ EDIT (attach wording) ☐ DEFER — owner: ________ date: ____

### D-5(b) — Marker keeper-snapshot policy: by-design snapshot vs re-key (ONE policy, not per-ISO)

**The fact pattern.** The marker format freezes "the run id frozen for the one-shot score"; all
three `complete` entries carry their keeper-at-declaration — PJM `pjm-140`, NYISO `nyiso-100`,
NEISO `neiso-54` (with the 2026-07-19 phantom-reaudit annotation re-pointing its train lineage to
`neiso-60`, keeper field unchanged) — while the dashboard keepers at this head are `pjm-143b`,
`nyiso109`, `neiso-72`. **Verified at this head: no rule-22 gate consumes the marker's `keeper`
field** (`scripts/lib/holdout_policy.py`, `run_calibration_full.py`, `legitimacy_diagnostics.py`,
`audit_keepers.py` key on block membership only) — the snapshot is a governance record, not an
enforcement input. **The freeze makes this non-urgent** (nothing is spendable while it stands);
deciding it now writes the spend protocol before the first post-lift spend needs it.

**Option A — by-design snapshot (recommended).** The keeper field is the declaration-time
evidence basis and is never edited by later promotions. At validation-spend time (post-lift,
owner-authorized), the spend session solves with the **then-current dashboard keeper** (rule 1:
most structurally faithful; rule 16: full span) and records which config it used as a new
annotation on the marker (e.g. `validation_spent_on`) in the spend session. Determination text
stays truthful — PJM's "CALIBRATED, zero caveats" was scored at `pjm-140` and keeps saying so.
Precedent: NEISO's annotate-don't-re-key trail. Cost: a reader may mistake the snapshot for the
spend config — one clarifying sentence in the marker's `note` (an FFR-3B edit, if signed here)
closes that.

**Option B — re-key on promotion.** Every keeper promotion in a `complete` ISO edits the
marker's keeper field. Cost: governance-file churn at keeper cadence (~20 promotions in 10 days,
audit FR-21); each edit silently transfers a determination onto a run it was never scored
against — honest re-keying would need a determination re-verification per promotion; and it buys
nothing, since no gate reads the field.

**Recommendation:** Option A, plus the one clarifying sentence in the marker note.

**Sign-off:** ☐ OPTION A (+note sentence) ☐ OPTION B ☐ DEFER — owner: ________ date: ____

### D-5(c) — FLAG (not resolved here): tier-agnostic vs tier-aware enforcement wording

PJM's marker `locked_test` text says "**The CI marker gate is tier-agnostic**, so this clause is
the binding discipline … even though CI will not catch it." CLAUDE.md rule 22 (amended
2026-07-31) says enforcement is **TIER-AWARE since 2026-07-31**, and this is true at this head:
all three gates read the tier map from `scripts/lib/holdout_policy.py` (`complete`→validation,
`final`→locked-test, fail-closed on unknown years). The marker sentence is the stale half. This
packet flags it per its brief and does **not** edit the marker (a governance file). Disposition
options: authorize FFR-3B to correct the one sentence (recommended — a live governance file
should not understate its own enforcement), or leave this packet as the recorded reconciliation.

**Sign-off:** ☐ FFR-3B corrects the sentence ☐ leave as recorded — owner: ________ date: ____

---

## D-6 residue — FF-3D pair-evidence regeneration order (the NYISO C3c adjudication is DONE)

**Done, no decision:** the NYISO C3c adjudication closed 2026-07-31 — you accepted the ledgered
caveat ("I am comfortable with taking c3c as a caveat…", marker `by` verbatim); NYISO is
CALIBRATED-WITH-CAVEATS (1 ledgered caveat of a budget of 3) with a validation-tier marker.

**What remains: order the regeneration of the FF-3D pair evidence, or wontfix it.** The facts:

- FF-3D (2026-07-18) implemented R5a Option B — the NYCA ICAP→UCAP translation 0.8679, NYSRC
  2025-26 IRM Study Appendix D Table D.2, reconciled two independent ways. **The pairing itself
  is a data citation and is NOT tainted.**
- The **pair evidence is** (rule-11 taint, FF-2C's stated NYISO-exclusion ground): the
  fixed-vs-curve-ON legs were scored against the pre-correction NYISO outage envelope — before
  the 2026-07-19 detector consolidation (which withdrew NYISO's first marker), the 2026-07-24
  uniform-detector extracts, the 2026-07-26 merit-order guard, the entire nyiso-96→100→109
  re-calibration, the 2026-07-30 downstate forecast-parity wiring, and Wave-1's FR-7/FR-8
  availability fixes.
- The pair's **structural finding stands regardless**: curve-ON NYISO without the LCR/TSL
  local-capacity floor and the CHP steam-following floor false-retires 2.28 GW of downstate
  `gas_st`/CHP steam (FF-3D §5.4/§6) — that prerequisite travels with any future flip, and the
  NYISO clearing flip itself is **not** in this batch.

**Option A — schedule, sequenced after D-1/D-2 (recommended).** Fold the regeneration into
FFR-3A (its step-0 D-6 line + battery): a NYISO fixed-vs-curve-ON T1-H pair at the
post-decision HEAD. Regenerating before FFR-2B/D-1/D-2 would measure a retirement/entry posture
this sitting is about to change and would burn the two multi-zone legs twice (rule 12 budget).
T1-H as specified is outside the freeze's scope (pack §0a); scoring stays in the T-R bands,
never widened.

**Option B — wontfix.** Leave NYISO curve-OFF indefinitely on the fixed net-CONE stub (the
fixed-mode arithmetic the gap register's BLK-9 row documents persists for NYISO); the 2026-07-18
pair evidence stays labelled tainted and is never cited. Defensible only if you intend never to
flip NYISO clearing.

**Recommendation:** Option A.

**Sign-off:** ☐ SCHEDULE via FFR-3A ☐ WONTFIX ☐ DEFER — owner: ________ date: ____

---

## D-7 — Golden-run posture (TWO sub-questions)

### D-7(i) — Golden-fixture reseed authorization (one 15-solve-year invocation)

**The fixture:** `tests/golden/ercot_2026_2040.json` — the ERCOT reference scenario, 2026–2040
(**15 solve-years**), banded CO2/capacity/price/cost/builds regression goldens. Seeded
2026-07-12 (P-3A horizon extension) — before every Wave-1 behavior fix (FR-1/2/7/8 change
forecast output) and before any decision above. FFR-1D (2026-07-31) made the staleness
**declared instead of silent**: a config-identity test plus a dated waiver
(`tests/golden/staleness_waiver.json`) that names this D-7 route and **expires 2026-10-31**; the
seed CLI is now schedulability-guarded (15 solve-years > the §2.1b 5-year cap → refuses without
its own written authorization).

**Cost anchor (measured, FF-3E §6):** ERCOT T1-F median 144 s/solve-year; projected full-horizon
(25-yr) wall 2.0 h, peak RSS 4.6 GB. The 15-year reseed sits below that projection (single-ISO,
pairable).

**The ask:** authorize **one** reseed invocation
(`python scripts/golden_forecast_bands.py seed --force --reason "<the signed decision set>"`),
executed inside FFR-3A **after** step 0 completes, so the fixture reflects the decided posture —
reseeding before the flips would force a second 15-year burn. Session-logged per §2.1b(d).
Deadline pressure: the waiver expires 2026-10-31.

**Sign-off:** ☐ AUTHORIZE (execute post-FFR-3A-step-0) ☐ HOLD — owner: ________ date: ____

### D-7(ii) — Weather posture for eventual goldens (peer review §3.3.3; audit FR-17)

**The question.** Any single solve is conditional on one pinned weather year (default 2024) for
demand shape, renewable CFs, and hydro. The ensemble machinery exists (`market-sim ensemble` over
the verified per-ISO weather pool; the copula sampler's weather/hydro dims) — what is missing is
a **decided posture for the golden runs** (which stay §2.1b-deferred; this decision schedules
nothing):

- **(a) Single-draw golden, labelled weather-conditional.** Cheapest; the standing disclosure
  list (peer review §4) already carries the label sentence. The peer review's position: a
  single-draw golden **is defensible only with the label**.
- **(b) Weather-year ensemble golden** at ~N× compute, N = the ISO's verified weather-pool size.
  Produces a distribution over weather rather than one draw; the reliability-grade commercial
  contrast (SERVM-class sweeps) is the peer review's anchor.

The choice also shapes D-7(i)'s labelling (a single-draw reseed carries the weather-conditional
label) and the compute ask of any future T3 authorization.

**Recommendation:** none dressed as default — the trade is compute vs a weather distribution,
and it is yours. The minimum defensible posture per the peer review is (a) **with the label**.

**Sign-off:** ☐ (a) single-draw + label ☐ (b) ensemble golden ☐ decide at T3 authorization —
owner: ________ date: ____

---

## After the sitting

FFR-3A step 0 executes each **signed** decision as its own commit citing the signature (D-5
residue actions ride FFR-3B, not marker files); then §W1-X (if still outstanding) + any Wave-2
epoch debt is cleared, and the consolidated re-baseline battery re-scores every board at the
post-decision HEAD (audit §4 Phase 3). Deferrals re-scope FFR-3A step 0 to the signed subset.
Nothing here touches the holdout freeze, whose lift remains a separate owner act outside this
program.

---

## Addendum F — **The G-31 rule-19 ruling is SIGNED, and the rule-12 concurrency reading is CORRECTED** (workstream manager, 2026-08-03, HEAD `01b6a6a`)

Read this addendum with C, D and E; together they supersede the packet body. Two owner
decisions were taken 2026-08-03, one substantive and one procedural. The procedural one
changes how much of this program can run at once, so it is recorded with the same weight.

### F.1 — D-8: queue latency and queue throughput are **TWO mechanisms**. The G-31 fix lane is **CHARTERED**.

**The question put.** FFR-3C (`docs/handoffs/ffr-3c-collapse-attribution-2026-08-03.md` §1.2,
§6.2) established that the R-NEW retirement redesign replaced a mechanism carrying **both** a
queue-latency term and a queue-throughput cap with one carrying **only** the latency term, on
the argument that rule 19 `[R-ONE-MECH]` — *"the same physical queue, carried once"* — makes
them one phenomenon. The consequence is measured and is not small: with only a latency term,
**exit-wave width is invariant at exactly one year no matter how many units fail**. The model
therefore has no representation of the constraint that stops a real ISO deactivating 21 GW in
a single year, while it *does* have one, armed and correct, for the constraint that stops it
**building** 21 GW in a single year. That asymmetry — exit throughput uncapped, entry
throughput capped at 2× the measured record — is what FFR-3C attributes the **depth** of the
reserve-margin trough to (ERCOT −1.5 %, CAISO −3.1 %; model single-year exits run **1.6×–4.8×
the largest single-year deactivation these ISOs have ever recorded**).

FFR-3C's §6.2 made the ruling a precondition: *"A throughput cap must not be armed by a session
that has not obtained that ruling — otherwise it is exactly the stacked-floor pattern rule 19
exists to prevent."*

**SIGNED: TWO MECHANISMS.** Latency and throughput are distinct phenomena for rule-19 purposes.
A throughput term may be armed alongside the existing lag without constituting a stacked floor.

**What this authorizes, and its bounds.** The G-31 fix lane is chartered to FFR-3C §6's
specification, with these bounds carried from that specification and from the standing rules:

1. **The G3 cap-grain defect is fixed FIRST and separately.** The pipeline's admission cap tests
   the *decision* year's requirement against exits that execute 1–3 years later (§1.2: **+10.3 %
   of requirement unseen** in the synthetic). Threading the execution year into that one call
   needs **no new parameter** and is cheaper than the cap; the throughput mechanism is measured
   against a corrected cap, not a broken one.
2. **The throughput term is EXTERNALLY IDENTIFIED, never fitted.** Source: max observed
   single-year per-ISO thermal deactivation from the EIA-860 retired sheet — measured at MISO
   7.57 GW, PJM 5.24, ERCOT 4.42, CAISO 1.48, NEISO 0.45, NYISO 0.31 (medians 3.54 / 1.32 /
   0.39 / 0.05 / 0.02 / 0.03). Rule 13 `[R-MEASURED]` admissible (it regenerates for a forward
   year from source data and responds to changed conditions) and rule 23 `[R-FROZEN-DERIVE]`
   compliant (re-derives on an EIA-860 vintage update, **never** because a residual moved).
   The reader exists as `scratchpad/measure_exit_throughput.py` in FFR-3C's record and moves to
   a `data/` module beside `build_throughput.py`, its exact entry-side analogue.
3. **Test set is ERCOT + PJM. MISO is excluded, by evidence.** ERCOT is the failing I6 case
   (26.8 %) and the only ISO where D-1 is attributed against a control; PJM carries the largest
   measured wave (12.68 % legacy → 8.55 % pipeline). MISO retires **nothing** economically in a
   T1-F window and is structurally incapable of exercising an exit-throughput mechanism —
   FFR-3C §3.2. Rule 25 `[R-ISO-SCOPE]` forbids importing any ISO's verdict to another.
4. **Leave-one-year-out within 2023–2025 before promotion** (rule 22), and the T1-F
   re-measurement is **paired against a control** — FFR-3C §3.2 is the standing proof that an
   ISO can be structurally incapable of exercising the mechanism under test, which an unpaired
   measurement cannot detect.

**What this decision does NOT do.** It does not lift the FH-4/FH-5 block, promote anything,
unarm D-1 or D-2 (Addendum D's HOLD PROMOTION, FIND ROOT CAUSE stands — both mechanisms **stay
armed**), or license tuning the cap to close the ERCOT/CAISO trough. The block lifts only when
a retirement-lane fix **lands** and FH-1's §3.3 gate **re-probes green** — characterizing was
never sufficient, and neither is chartering.

### F.2 — Rule 12 `[R-PARALLEL]` concurrency: the cap is **per prompt, not per program**

**Owner, verbatim:** *"These run in separate sessions so there's no limit to solve slots as long
as there's only 2 per PROMPT."*

The manager had been reading rule 12's concurrency cap as a **program-wide** budget of two
simultaneous solve invocations, and had been serializing lanes and pairing only no-solve work
against a solve lane on that basis. **That reading was wrong and is corrected here.** The cap is
**per session**: each dispatched session may run up to ~2 concurrent solve invocations, and
independent sessions do not draw against each other, because they do not share a container.

**What survives unchanged — the machine limits, which are per-container and therefore per
session:**

- Years run **sequentially within a single invocation**, always. The `runner.py` year loop is
  intentionally sequential and is never parallelized; one year's LP already holds several GB.
- **≤2 concurrent solve invocations WITHIN one session**, and **≤2** for per-plant multi-zone LPs.
- **PJM and MISO legs never co-run within a session** (~8.6 GB peak RSS each).
- **≤5 solve-years per invocation** (owner standing instruction + forecast plan §2.1b) —
  untouched by this correction.

**Consequence for dispatch, stated plainly:** the program is no longer throughput-limited to one
solve lane at a time. Lanes that were queued *solely* because "the battery owns the solve slots"
— FFR-SC (FF-G1 transmission A/B) and the FFR-SA close-out (PJM smoke table) — dispatch
concurrently with the battery rather than behind it. The reason to hold a lane back is now
evidence dependency or owner decision, never slot contention.

**Bookkeeping.** Where an earlier record in this program says a lane waits for a solve slot, that
statement rests on the superseded reading. It is corrected by this addendum and not by rewriting
the earlier record — the same convention as Addenda A–E.

---

## Addendum G — **The D-8 wave landed; the FH gate went green for the wrong reason and the block does NOT lift** (workstream manager, 2026-08-03, HEAD `9aca82b8`)

Four lanes dispatched under Addendum F landed within hours: **FFR-3F** (the G-31 fix),
**FFR-3A-2** (the battery close), **FFR-SC** (the transmission A/B) and **FFR-PA** (the
retirement registry). Two of them committed **incomplete deliverables with `(pending)`
placeholders** because their solve lanes had not finished at merge. This addendum records what
is established, one manager determination, and one decision the owner needs.

### G.1 — D-8 executed. Both mechanisms are built, registered, default-off, and MEASURED INERT in ERCOT.

FFR-3F (`docs/handoffs/ffr-3f-exit-throughput-2026-08-03.md`) discharged the D-8 charter to its
bounds:

* **The G3 cap-grain fix landed** (`2adfb49`). The pipeline's admission cap now resolves its
  adequacy requirement at the schedule's **execution horizon** rather than the decision year —
  both the delivery year and the projected peak. No new parameter, pinned by a discriminating
  test (decision-year grain retains 1 unit, execution-year grain retains 2), byte-inert where
  the grain was already right.
* **The exit-throughput cap landed default-OFF** (`db5ff91`), externally identified from the
  EIA-860 retired sheet and reproducing D-8's cited values exactly (ERCOT 4.42 GW/yr, PJM 5.24).
  The synthetic is decisive on the property that was missing: FFR-3C's 12-unit cohort exits in
  **one** year uncapped and over **three** capped, **total identical** — the cap moves the
  calendar and does not touch the level.
* **Both are PROVABLY INERT at the ERCOT T1-FF gate posture, against a paired pre-fix control.**
  All three arms are identical to the megawatt in every year, with **zero `pipeline_events` of
  any kind** — no ERCOT unit fails the going-forward bar anywhere in the window, so the
  retirement pipeline is never entered. Per the lane's own charter this is a **NULL, not a
  pass**, and the pairing is what makes it legible.
* **PJM is where the seam is live**: 1,199 units fail the going-forward bar at the 2024 screen,
  the admission cap admits **9 (1.056 GW)** and un-admits **1,190 (108.2 GW)**. The cap is the
  binding constraint on PJM's exit membership by two orders of magnitude — exactly the quantity
  FFR-3C said was being tested against the wrong year.

### G.2 — MANAGER DETERMINATION: FH-4/FH-5 stay BLOCKED. The re-probe's green is not the gate's.

FH-1's §3.3 acceptance gate re-probes **I6 PASS / I7 PASS / I12 WARN** at the post-fix HEAD,
against the recorded **FAIL / FAIL / WARN**. On the letter of the gate that is a pass. The lift is
the manager's call and I am **not** taking it. FFR-3F declined to claim it and gave the reasons;
I adopt them:

1. **The green is not the fix's.** The pre-fix control returns the identical PASS/PASS/WARN.
   Nothing FFR-3F built moved I6 or I7. The flip is attributable by elimination and mechanism to
   **D-1's `legacy` → `pipeline` default flip, signed 2026-08-02 — after FH-1's probe ran.**
2. **I12's WARN has INVERTED SIGN — a new problem wearing the old problem's label.** FH-1 exited
   the band *downward* (an over-retiring harness). The re-probe exits it *upward*: 2024 at
   32.3 % and 2025 at **40.2 %** against a ceiling of 28.7 %. The harness has swung from retiring
   26.8 % of its thermal fleet in a single year to retiring **nothing at all** while capacity
   keeps being added. The gate's own wording — *"an over-retiring harness would make every
   downstream metric uninterpretable"* — applies with equal force to a harness that cannot retire
   anything.
3. **The gate cannot exercise what it was re-probed to test.** Zero `pipeline_events` means the
   retirement layer is **untested** at this posture, not validated by it.

**And a fourth reason, which is the one that turns this from a measurement into a decision.**
FFR-3F §5.1 establishes a **mechanical impossibility**: under the pipeline rule a unit decided at
the 2024 screen with `L_coal` = 3 executes in **2027**, and one decided at the 2025 screen
executes in 2028 — **both outside a 2023–2025 window**. Even if ERCOT units *had* failed the bar,
**the pipeline rule cannot produce a single retirement execution inside a 3-year T1-FF window.**
The gate as currently cut can therefore never test the retirement layer under the shipped rule,
whatever the result. A green here means "the window is too short to see anything," not "the
harness is sound." That is not a threshold to re-tune; it is a gate that needs re-cutting, and
how to re-cut it is the owner's call (see G.5).

### G.3 — FFR-3A-2: the collapse REPRODUCES cold, and BLK-10 is scorable for the first time

* **The D-1/D-2 adequacy collapse reproduces** cold and post-epoch. It is not a cache artifact.
* **BLK-10 backstop sizing is measurable at last** — the evidence D-2 was signed to re-open and
  which had been SKIPPED on every leg at FF-2D and FFR-3A. **CAISO builds 65.5 % of its capacity
  additions through the administrative reliability backstop** (rubric pass bar 10 %; the
  rubric's own rationale calls this channel "a single-digit-percent residual in real markets").
  FC-2 row 4 **FAILs** for CAISO; NYISO 23.8 % and NEISO 11.7 % are CAVEATs; **ERCOT is 0.0 % in
  BOTH arms**.
* That last number **sharpens FFR-3C's attribution**: ERCOT's collapse is not a backstop-sizing
  story at all, it is entirely the retirement/entry asymmetry. The backstop finding belongs to
  CAISO and the downstate/New-England ISOs, and rule 25 forbids carrying it across.
* **FF-3E part c (kill-resume) is now FAIL** where FF-2D recorded GREEN for all six ISOs: the
  first freshly-solved year after a resume has **identical aggregates and identical evolution
  counts but different byte hashes** on both dispatch and price. A resumed full-horizon run is
  therefore not bit-reproducible against an uninterrupted one — a live provenance risk for any
  T2/T3 campaign, where resume is not optional at 7–10 h/ISO. Two candidate mechanisms (array
  ordering vs alternate optima) and the discriminating test are named; attribution is not claimed.

### G.4 — Two deliverables are committed INCOMPLETE, and one instrument correction matters

* **FFR-3A-2 §§3.4, 4.2, 5, 7, 9 are `(pending)`** — T1-H measured results, T1-X measured
  results, FC-6 driver response, the §2.1b gate scorecard, and the not-measured list. Its T1-X
  fold test ran and returned **all three legs RE-RUN** (no leg folds as-is). No board was
  regenerated and nothing was registered.
* **FFR-SC §§2–5 are placeholders** — the CAISO paired arms had not finished. §1 stands and is
  a real result: **PJM is provably inert for the transmission gate with no solve spent**, because
  all six live PJM rows carry `delta_mw = 0.0` (PJM publishes component lists, not interface-TTC
  deltas, and rule 5 forbids inventing the MW). CAISO is the only ISO that can test it.
* **FFR-3D's FC-7 repair was itself broken and is now fixed** (`ea7cd5d`): `write_run_config`
  crashed on every real T1-F leg. FFR-3A-2 also **retracted its own cache-key finding** — it had
  measured the wrong object, because a *request-side* `cache_key()` is not the key a run is
  recorded under. That distinction is documented only inside a docstring and is now an open
  blocker in its own right.
* **`uv sync` is an undocumented hard prerequisite.** The container ships no Python environment;
  the failure surfaces as *"50/50 datatype(s) failed"* from `regenerate_clean.py`, which reads
  as a data problem and is not one. Budget ≈2 min (env) + ≈65 min (clean). On the `uv` path the
  documented `tzdata` / `ZoneInfoNotFoundError` trap does **not** arise — that one is specific to
  a bare `pip` environment.

### G.5 — OPEN DECISION for the owner: how to re-cut the FH-1 §3.3 gate

Put in G.2's terms: the gate is now known to be **structurally incapable** of testing the thing
it exists to test, because the shipped retirement rule's execution lag exceeds the gate window.
Options, with the manager recommendation named:

* **(a) Re-cut the gate to the longer window already in the FH plan** — base 2021 → 2021–2025.
  Five years accommodates `L_coal` = 3, so a decision inside the window can execute inside it and
  the retirement layer becomes observable. **Recommended.** Cost: the longer window is 5
  solve-years (at the standing per-invocation ceiling, so it fits) and needs a rule-22 legality
  check on 2021–2022, which FFR-3A-2 §3.3 has already shown is checkable rather than assumed.
* **(b) Re-cut the gate's criterion** to something a 3-year window can test — e.g. gate on
  `pipeline_events` *decided* rather than *executed*. Cheaper, but it measures intent rather than
  effect and would not have caught the original 21 GW lump.
* **(c) Lift the block on the letter of the current gate.** I think this is wrong and want its
  cost recorded: it would unblock FH-4/FH-5 on a probe that measured a harness retiring nothing,
  with reserve margin 11.5 pp above its ceiling, and no test of the retirement layer at all — the
  precise failure the gate was written to prevent, inverted.
* **(d) Keep FH-4/FH-5 blocked with no gate change.** Honest, and the status quo this addendum
  records, but it leaves the capacity-expansion skill measurement the peer review names as
  bucket-C item 7 permanently unobtainable.

**Sign-off:** ☐ (a) longer window ☐ (b) re-cut criterion ☐ (c) lift on the letter ☐ (d) stay
blocked — owner: ________ date: ____
