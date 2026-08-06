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

### G.6 — G.5(a) is independently corroborated by FFR-3F's PJM half, and its posture is already legality-checked (manager, 2026-08-03, HEAD `01bb25f7`)

FFR-3F continued after Addendum G was written and completed the PJM pairing it owed. Three
results change what G.5 is choosing between, so they are recorded here rather than left in the
lane doc.

1. **The cap-grain fix is emphatically NOT inert — ERCOT simply had nothing for it to act on.**
   In PJM it changes the admitted exit set by an order of magnitude and in exactly the direction
   FFR-3C §1.2 G3 predicted: the old grain tested the schedule against a requirement ~10 % too
   low and over-admitted; the corrected grain retains **13.7 GW more capacity** in the pipeline
   screen — an **89–93 % cut in admitted exits** (pre-fix 83 units / 14.766 GW, cap-fix 9 units /
   1.056 GW). G.1's "provably inert" was true **of ERCOT only** and must not be generalized.
2. **The throughput cap is a measured NULL in BOTH test ISOs, and has still never bound in any
   full solve.** Same underlying reason, different routes: ERCOT never enters the pipeline at
   all; PJM enters it and then every admitted unit re-clears the bar and reverses through the
   soft latch before its execution year (83 → `reversed` pre-fix, 9 → `reversed` cap-fix). The
   cap acts on the year's `due` set and `_apply_exit_throughput_cap` is only invoked when that
   set is non-empty, so it is never called. Predicted-inert and measured-inert are different
   claims; this is now the second.
3. **Realized exits are 0.000 GW in every arm of both ISOs, and in-window dispatch skill is
   untouched** (PJM C1 12.230/18.843, C3a 0.318/49.688/2.564 — identical across arms), because
   nothing the corrected grain changes ever reaches the LP inside a 3-year window. The membership
   change would first surface as executions in **2026+**.

**Why this bears directly on the sign-off.** FFR-3F's own §10.1 reaches G.5's conclusion
independently and states it as measured rather than suspected: *"The T1-FF 3-year window is the
wrong instrument for testing exit mechanisms."* It names the posture G.5(a) would adopt — the
**T1-H 2021–2025 vintage-2020 posture FFR-2B already used**, where PJM's pipeline coal wave was
**14.756 GW** — on the ground that a 5-year window clears `L_coal` = 3 with room to spare. And
**FFR-3A-2 §3.3 has already checked that window's rule-22 legality rather than assuming it**, so
option (a) carries no unresolved holdout question.

This does not change the manager determination in G.2 — **FH-4/FH-5 stay blocked** — and it does
not pre-empt the owner's choice among (a)–(d). It removes the two objections a reader might
reasonably have raised against (a): that the longer window was the manager's preference rather
than an evidenced requirement, and that its rule-22 status was open.

**One question G.5 does not cover and nobody currently owns** (FFR-3F §10.4): the FH-1 gate's
**I12 inversion is unattributed**. ERCOT now runs 40.2 % reserve margin against a 28.7 % ceiling
while retiring nothing. Whether that is the pipeline rule under-retiring, the entry side
over-building, or the ERCOT band's known 6.65 pp basis mismatch (FFR-3C §2.1) has not been
separated by any lane.

---

## Addendum H — **The battery is CLOSED and registered; CAISO's backstop is diagnosed; a SECOND decision now converges on the same answer as G.5** (workstream manager, 2026-08-04, HEAD `a0bf3db3`)

Five lanes dispatched after Addendum G all ran: **FFR-3A-3** (battery close), **FFR-3H** (CAISO
backstop), **FFR-SC-2** (transmission A/B), **FFR-SA-close** (PJM load-shape smoke) and
**FFR-3J** (kill-resume instrumentation). Zero open PRs. This addendum records what closed, one
new owner decision, and the convergence between it and G.5.

### H.1 — The T1 battery is CLOSED, scored and REGISTERED

FFR-3A-3 filled every `(pending)` section and discharged the registration duty FFR-3A-2 left
open: **18 hindcast sidecars** plus `ff-verdicts.json` are committed. The headline from the
regression table against FF-2D:

* **No determination moved. All six were HOLD at FF-2D; all six are HOLD now.** FC-1, FC-3,
  FC-4, FC-5, FC-6 and FC-7 are unchanged in every ISO. **Every movement is inside FC-2**, and
  it separates into three causes that must not be conflated: genuine movement from the signed
  decisions (ERCOT row1 CAVEAT→FAIL and row6 sustained-VOLL newly firing, both **attributed
  against the paired control**; CAISO row1 CAVEAT→FAIL as an **observation, not attributed**);
  newly-scorable rows; and one genuine improvement.
* **⚠ The newly-scorable rows are NOT regressions.** FC-2 row 4 was SKIPPED everywhere before
  `34c2f25` + `0830d134`. Reading CAISO 65.5 % / NYISO 23.8 % / PJM 23.6 % / NEISO 11.7 % /
  MISO 9.2 % / ERCOT 0.0 % as "FC-2 got worse" would be wrong: **the metric did not move, the
  instrument started reporting it.** Without the fix every one would have read a false
  `PASS 0 %`.
* **⚠ THE FIRST POSITIVE EVIDENCE FOR D-2, and it deserves to be seen.** MISO's FC-2 row 3
  moved **FAIL → PASS**: the FF-2C-induced `gas_ct` cobweb the mechanism matrix records is
  **gone** at this HEAD. `entry_commissioning_lag` is D-2's structural anti-cobweb — decide at
  Y, commission at Y+2, so decision and commissioning separate and the oscillation damps.
  FFR-2B could not test the claim and said so; **MISO's FF-2D leg is the one case in the
  program where it was testable at all.** Stated at the right strength by the lane and repeated
  here: this is **CONSISTENT WITH** the anti-cobweb claim, **not an attribution** — the two legs
  differ in more than D-2 and no paired control was run. It is nonetheless the first measured
  result pointing *for* D-2 in a battery otherwise dominated by adverse D-2 findings, and the
  owner should weigh it against them rather than only against them.

### H.2 — CAISO's 65.5 % is diagnosed: three stacked causes, and the prompt's hypothesis was refuted-then-sharpened

FFR-3H (`docs/handoffs/ffr-3h-caiso-backstop-2026-08-04.md`), diagnosis only, nothing fixed:

1. **~37 pp is a BOOKING-CONVENTION ARTIFACT of the row-4 ratio** — the backstop books in-year
   while economic entry books at decision + 2. Measured: 65.48 % → **28.61 %** with the
   commissioning lag unarmed as a labelled probe arm.
2. **The residual ~29 % is real**, and its cause is specific: a CAISO `gas_ct` is `unprofitable`
   in the economic entry screen **in every year of every arm**, by **$39,974–45,316/MW-yr**. The
   administrative channel is the only one that can add firm capacity.
3. **47 % of the total backstop build closes a deficit the model already has in its BASE YEAR** —
   2026 accredited firm 50,729 MW against a 57,306 MW requirement, **before any evolution step
   runs**. That is an accreditation-ledger question, not an entry question.

**The growth ladder is NOT the cause** — unarming it moves the cumulative share 0.84 pp while
completely re-phasing the build, independently reproducing in CAISO the "re-phases, cumulative
invariant" result FFR-2B measured in MISO (measured separately per rule 25, not transferred).

**ERCOT's 0.0 % now has its mechanism:** `resolve_reserve_margin_build_enabled(ERCOT) = False`.
ERCOT is not in the population at all, so its 0.0 % is structural and FFR-3C's
retirement/entry-asymmetry attribution for ERCOT stands untouched.

**Two findings inside it that outlive the diagnosis.** (a) **A net-CONE level re-anchor would
not fix this**, and that is the most decision-relevant thing about the candidate: CAISO's
$88.08/kW-yr is current and correctly cited (FF-2C R4), but the CPM soft-offer cap is *a price
cap on CAISO's own administrative backstop procurement* — not a market-clearing capacity price
and not a net-CONE. The model prices CAISO capacity at the administered price of CAISO's own
backstop and then closes two-thirds of its gap with that backstop. What the parameter cannot do
is **vary**, and it is the invariance, not the level, that binds. (b) **Rule 14 finding:** the
ISO with the most elaborate published VRE accreditation in the country — CPUC slice-of-day /
ELCC — is accredited in this model on a **generic non-CAISO flat fallback** (solar 0.18, wind
0.16, invariant across a 0.2×–2.0× penetration sweep), because `RENEWABLE_ELCC_CURVES_BY_ISO`
holds PJM/MISO/NYISO only and `RENEWABLE_CAPACITY_CREDIT_BY_ISO` holds ERCOT only. Direction
unresolved, so it is filed as an open ledger question rather than a shortfall.

**And a structural observation worth carrying:** CAISO retires 1,492.5 MW of `gas_st` in a single
year (2027 — a **98.8 % single-year class exit**) plus 1,122 MW of nuclear in 2030. That is
FFR-3C's G-31 asymmetry reproduced in CAISO, but it **expresses differently**: in ERCOT, backstop
OFF, the asymmetry produces a *collapse*; in CAISO, backstop ON, it is absorbed by step 6 and
surfaces as *administrative over-build*. **Same defect, two symptoms, because of one gate.**

### H.3 — Both remaining gate A/Bs are INERT, and one is inert for a reason worth more than the verdict

* **FFR-SC-2:** the transmission-expansion gate is **inert in CAISO 2026–2030 and provably inert
  in PJM 2026–2050**. CAISO's inertness is *structural*: `WECC_import_simultaneous` caps the
  **signed sum of two legs that run in opposite directions**, so it stays slack even when both
  legs are individually saturated — **the registry uplifted the one element that cannot bind.**
  No default flipped; arming stays the owner's box and nothing argues for it.
* **FFR-SA-close:** the owed PJM load-shape smoke ran, off-leg 2026–2028, all invariants PASS.

### H.4 — NEW OWNER DECISION (D-9): D-2's commissioning lag CENSORS half the T1-H scoring window

Spelled out before it is named, because it is easy to misread as a metric problem: T1-H scores
the years {2023, 2024, 2025}, but `ENTRY_COD_LAG_YEARS = 2` sends the **2024 and 2025 entry
decisions to commercial operation in 2026/2027 — outside the scored window.** So **half the
solved decision years cannot score at all, by construction.** Additions bands are mechanically
suppressed against any pre-D-2 bundle regardless of actual entry skill, and a cross-boundary
additions comparison is **not like-for-like**. This currently affects the interpretation of every
T1-H additions verdict, including MISO's — whose FC-3 now fails on the censored half alone.

This is a **design decision, not a parameter** (so it is not tunable and must not be treated as
one). Two routes:

* **(i) Lengthen the T1-H window** so a decision inside it can commission inside it.
* **(ii) Score COD-shifted additions** — attribute an addition to its decision year rather than
  its COD year.

**⚠ THE CONVERGENCE THE OWNER SHOULD SEE: D-9(i) and G.5(a) ARE THE SAME ACTION.** Two
independent blockers, discovered by different lanes on different evidence, both resolve by moving
to a **five-year window**: G.5 because `L_coal` = 3 exceeds a 3-year exit window, D-9 because
`ENTRY_COD_LAG_YEARS` = 2 exceeds a 3-year entry window. The model's own execution lags are
simply longer than the windows it is being scored on, on **both** the exit and the entry side.
Signing G.5(a) very likely disposes of D-9 as well; signing G.5(b), (c) or (d) leaves D-9 live
and needing its own answer. **Recommendation: take them together, as (a) + (i).**

**Sign-off D-9:** ☐ (i) lengthen the window ☐ (ii) score COD-shifted ☐ take with G.5(a) —
owner: ________ date: ____

### H.5 — What is open, and who owns it

| # | Item | Owner |
|---|---|---|
| 1 | **G.5** — the FH-1 §3.3 gate re-cut | **OWNER, unsigned.** Gates every FH lane |
| 2 | **D-9** — the T1-H censoring window (H.4) | **OWNER, unsigned.** Converges with G.5(a) |
| 3 | FC-7 fails on EVERY T1-H and T1-X leg — `run_capacity_hindcast` writes `run_config.yaml`, FC-7 needs `.json`. The **unfixed analogue** of FFR-3D's blocker 7 | dispatchable; must land **before** the next battery |
| 4 | ERCOT T1-X price-2025 regressed 8.6 % PASS → **22.5 % FAIL**, sole regressor of three legs, unattributed | dispatchable (needs a paired control) |
| 5 | FF-3E part c — FFR-3J built the discriminator but **never ran the drill**; still unadjudicated | dispatchable, small |
| 6 | The FH-1 I12 inversion (G.6) — unattributed | dispatchable |
| 7 | CAISO accreditation ledger — the 6,577 MW base-year deficit + the generic VRE credit (H.2) | dispatchable |
| 8 | D-2′ `entry_vre_capacity_revenue` — signed HOLD at Addendum C, **still never probed** | unowned |
| 9 | Pre-existing test failures on main | unowned |

---

## Addendum I — **G.5 and D-9 are SIGNED: the windows are lengthened, together** (workstream manager, 2026-08-04, HEAD `5055b1a5`)

Both open decisions were put to the owner as decision cards and both are signed. They are
recorded here as one entry because the owner took them as one action.

| # | Decision | Signed | Effect |
|---|---|---|---|
| **G.5** | Re-cut the FH-1 §3.3 acceptance gate | **(a) LONGER WINDOW** | The gate moves to the five-year 2021–2025 / vintage-2020 posture |
| **D-9** | The T1-H censoring window | **TAKE WITH G.5(a)** | One action; the T1-H window lengthens with it |

**What the owner accepted, in plain terms.** The model's own execution lags are longer than
the windows it was being scored on, on **both** sides: `L_coal` = 3 exceeds a three-year *exit*
window and `ENTRY_COD_LAG_YEARS` = 2 exceeds a three-year *entry* window. A gate that cannot
produce a retirement execution, and an additions band that cannot score half its own decision
years, are the same defect seen from two ends. Five years fixes both.

### I.1 — What this decision does NOT do

* **It does NOT lift the FH-4/FH-5 block.** The block lifts on a **landed fix plus a green
  re-probe** (Addendum G.2, unchanged). Signing G.5(a) authorizes the gate to be *re-cut and
  re-probed*; it does not pre-approve the result. A session that reports the re-probe green
  does not thereby unblock FH — the lift remains the manager's, on the re-cut gate's evidence.
* **It does NOT spend a holdout marker, and it must not.** `final` stays EMPTY, the holdout
  spend freeze stays ACTIVE, and NEISO's locked test stays SPENT. The five-year window is legal
  by a **carve-out**, not by a marker.
* **It does NOT authorize tuning to the re-cut gate.** Rules 1/11/14 apply unchanged: if the
  re-probe fails, that is a finding written up, not a threshold moved.
* **It does NOT retroactively validate anything scored on the three-year window.** Every
  committed T1-H additions verdict was produced under the censoring described in H.4 and stays
  interpreted that way until re-measured.

### I.2 — The rule-22 position: one half is verified, the other half is NOT, and the difference matters

**Verified, for T1-H.** FFR-3A-2 §3.3 checked the 2021–2025 window against the code rather than
the prose, and `scripts/lib/holdout_policy.py` carries an explicit enumerated
capacity-hindcast carve-out: `HINDCAST_SEED_YEARS = {2021}` (solvable, **never scored**),
`HINDCAST_BRIDGE_YEARS = {2022, 2026}` (evolved across, **never solved, data never read**),
`HINDCAST_SOLVE_YEARS = {2021, 2023, 2024, 2025}` — four solve-years, under the ≤5 cap — with
scoring bounded to 2023–2025 on both sides and `_validate_window` enforcing it fail-closed.
**No marker is spent and the freeze is not implicated.**

**NOT verified, for T1-FF.** The FH-1 gate runs the *other* harness (`--forward-from-base`), and
whether the same carve-out enumerates a **base-2021** T1-FF window has not been checked by any
lane. The FH plan names base 2021 → 2021–2025 as its second phase, so it is *planned*, but
planned is not enumerated. **The lane must verify this against `holdout_policy.py` before
solving, and if the carve-out does not cover it, that is a GOVERNANCE QUESTION ESCALATED TO THE
OWNER — never a carve-out the lane adds for itself.** Widening a rule-22 carve-out to make one's
own window legal is precisely the move the policy exists to prevent, and this addendum does not
authorize it.

### I.3 — What is now dispatchable, and what still is not

The gate re-cut lane (FFR-3Q) is dispatched on this signature. **FH-4 and FH-5 remain blocked**
until it lands and its re-probe is green. The five lanes dispatched at H.5 (FFR-3K/3L/3M/3N/3P)
are unaffected and continue independently — none of them depends on this decision, and FFR-3N's
I12-inversion attribution becomes **more** valuable under the re-cut gate, not less, because the
inversion is one of the two things the re-cut is meant to make legible.

Still unowned after this signing: **D-2′'s probe row** (signed HOLD at Addendum C, never
probed) and the **pre-existing test failures on main**.

---

## Addendum J — **CORRECTION: the H.4 convergence was wrong on the T1-H side. D-9(i) is a NO-OP and D-9 is RE-OPENED** (workstream manager, 2026-08-04, HEAD `b45fc4e2`)

### J.1 — The manager's error, stated plainly

Addendum H.4 asserted that *"D-9(i) and G.5(a) ARE THE SAME ACTION"* and recommended taking
them together. **That was wrong on the T1-H half, and the owner signed D-9 on that
recommendation.** FFR-3Q Task 2 verified the actual T1-H window against all **57 registered
plain-hindcast sidecars**: **none starts anywhere but 2021, and none carries a `solved_years`
other than `[2021, 2023, 2024, 2025]`.** **T1-H has ALWAYS been at the five-year 2021–2025 /
vintage-2020 / four-solve-year posture that G.5(a) moves the T1-FF gate TO.**

So there is no shorter T1-H window to lengthen, no additions band becomes newly visible, and
**neither** "the model got better" **nor** "the metric can now see it" applies — because
nothing changed. The convergence recorded in H.4 **holds on the exit side only**: G.5(a) is
real and unaffected, D-9(i) is a no-op. The error was inferring the T1-H window's length from
the censoring symptom instead of reading the sidecars.

### J.2 — G.5(a) is unaffected and its blocking precondition is DISCHARGED

The exit-side half of the signature stands entirely. And FFR-3Q's **Task 0 came back
VERIFIED**, which was the one thing I.2 flagged as unchecked: the enumerated
capacity-hindcast carve-out in `scripts/lib/holdout_policy.py` **does** cover a base-2021
T1-FF window — `--forward-from-base` routes through the same `_validate_window`, whose
non-crossover branch applies the plain window rules (2021 floor, end ≤ 2025, `{2021}` seed,
2022 bridge) and re-checks fail-closed against `hindcast_solve_year_violations`. **Verified by
execution, not by reading prose. No carve-out was added or widened, no marker spent, the
freeze untouched.** That is the correct discharge of I.2's escalation clause, and the gate
re-cut proceeds.

### J.3 — The censoring SURVIVES, and no window length can remove it

This is the part that makes D-9 a live decision again rather than a closed one. FFR-3Q
established that the T1-H window cannot be extended in either direction:

* **Forward is closed by rule 22.** 2026 is locked-test tier, `final` is **EMPTY**, the
  holdout spend freeze is **ACTIVE**, and 2027 has no actuals to score against.
* **Backward is closed by data and by tier.** The 2021 demand-profile floor bounds it, and
  2020 sits in the validation tier.

So the D-9 censoring — half the solved entry-decision years unable to score because
`ENTRY_COD_LAG_YEARS = 2` pushes their commercial operation past the window — **is structural
and permanent under the current scoring convention.** Lengthening cannot fix it because there
is nowhere left to lengthen into.

**Only D-9(ii) — COD-shifted scoring, attributing an addition to its DECISION year rather
than its COD year — can recover the censored half. It is UNSIGNED.** FFR-3Q escalated rather
than implementing it, which is correct.

### J.4 — D-9, re-put to the owner

The option signed at Addendum I does nothing. The choice is now between the only two live
options, and it should be made knowing the first is permanent:

* **(ii) COD-shifted scoring.** Recovers the censored half. Cost: it changes what the
  additions metric means, and makes every historical additions verdict non-comparable to new
  ones — the FF-2D regression baseline stops being usable for additions specifically.
  **Recommended**, because the alternative is accepting that half of every T1-H entry
  measurement is permanently unscoreable, and an entry mechanism the program cannot measure
  cannot be validated at all.
* **(iii) ACCEPT THE CENSORING as a permanent, disclosed limitation.** No code change. Cost:
  every T1-H additions verdict — including MISO's FC-3, which fails on the censored half
  alone — carries a standing caveat forever, and D-2's entry-side skill is never measurable
  on this tier. If chosen, it belongs on the peer-review §4 standing disclosure list, not
  buried in a lane doc.

**Sign-off D-9 (re-put):** ☐ (ii) COD-shifted scoring ☐ (iii) accept as permanent disclosed
limitation — owner: ________ date: ____

### J.5 — Also landed, and worth the record

* **FFR-3Q additionally confirmed FC-7's yaml/json defect is STILL UNFIXED at this HEAD** —
  the H.5 item 3 lane (FFR-3K) has not run. It remains true that no T1-H or T1-X FC-7 verdict
  carries information about leg quality.
* **FFR-3P measured the CAISO NQC arm and RETRACTED TWO OF ITS OWN CLAIMS.** The
  "+1,735.8 MW thermal under-credit" and "+1,681 MW hydro under-credit" are both **wrong**:
  CAISO's published fleet thermal credit is 0.9537 against the model's 0.9457, so the model is
  **0.8 % ABOVE**, and a Pmax basis would over-credit by ~2 GW; the published fleet-wide hydro
  rate is 0.6936 against the model's 0.7041, already **1.1 pp generous**. Both errors came
  from inferring a partition where the ISO publishes the whole class's realized ratio. Neither
  claim had reached main. **The rule-14 "if it gets worse, keep it and open the root cause"
  branch never fired** — arming the identified VRE accreditation moved FC-2 row 4 from 65.48 %
  to 63.23 % (still FAIL) with zero invariant flips and retirements, renewable builds, storage
  builds and CO2 identical to the digit. The non-obvious finding: **2027–2029 do not move by a
  megawatt** because the backstop is RATE-limited there, not need-limited, so the entire
  −1,312 MW lands in 2030.
* **NYISO moved again** → `2026-08-04-nyiso-120-c119-scope`. That is the **seventh** NYISO
  keeper in four days.

---

## Addendum K — the FH-4/FH-5 lift call, D-9 re-signed, and a new decision D-10

**Written 2026-08-04 by the workstream manager at `origin/main` `145e4c5f`.** Supersedes
Addendum J where they conflict; J itself is untouched, per the correct-by-addendum discipline.

### K.1 — FH-4/FH-5: **NOT LIFTED. The block stands.** (manager determination)

This is the manager box that Addendum I.1 says only a manager opens. It is **not** opened,
and the reason is not a judgement call — the evidence the lift requires does not exist.

The lift requires two things: a landed fix **and** a green re-probe on the **re-cut** gate.
FFR-3Q was chartered to produce the second. **It did not.** Read at this HEAD:

| FFR-3Q section | state |
|---|---|
| §0 Headline | **`*(pending)*`** |
| §1 Task 0 — rule-22 legality of a base-2021 T1-FF window | **VERIFIED by execution** — delivered |
| §2.1 Task 1 posture, pairing, pre-registered reads | delivered (arms A `b99600bceb8cb6b8` / B `5c352508039513da`, one-field diff) |
| **§2.2 Task 1 Result** | **`*(pending)*`** — the arms were never solved |
| §3 Task 2 — D-9 | delivered (the no-op determination; became Addendum J) |
| §4 What this evidence does NOT separate | **`*(pending)*`** |

Corroborated against the artifacts rather than the prose, per J.1: `frontend/data/hindcast/`
holds **132** sidecars and **zero** named `ffr3q-*`. The only registered T1-FF gate leg is
`ercot-2023-2025-t1ff-armr-fh1gate.json` — the **original three-year** window. The re-cut
posture (base 2021 / vintage 2020 / 2021–2025) has never been solved.

So FFR-3Q delivered its legality determination and its D-9 escalation and stopped before its
central task. **The re-probe is re-dispatched as FFR-3Q-2.** Until its result lands and is
read against Addendum G.2's three binds — the earlier green was not the fix's; I12's WARN had
inverted sign; zero `pipeline_events` means untested, not validated — FH-4 and FH-5 stay
blocked. A green on a posture that cannot exercise the mechanism is still not a pass.

### K.2 — D-9 (re-put at J.4): **SIGNED — (ii) COD-shifted scoring**

Owner, 2026-08-04. Score an addition against the year the model **decided** it, not the year
it commissions. Scorer-side; needs no out-of-training year; recovers the censored half of
every T1-H entry measurement.

**The cost is accepted with the decision and must be carried in every subsequent report:** it
changes what the additions metric measures, so **every historical additions verdict becomes
non-comparable to new ones, and the FF-2D regression baseline stops being usable for additions
specifically**. Retirements-side comparability is unaffected. The implementing lane is
**FFR-3S**; it does not retro-edit committed artifacts and does not re-score committed legs to
pick up the change.

Rationale on record: the alternative (iii) meant accepting that half of every T1-H entry
measurement is permanently unscoreable, which makes D-2's entry-side skill unmeasurable on
this tier and leaves "FC-3 FAIL" unactionable — MISO's FC-3 fails on the censored half alone.

### K.3 — D-10 (NEW, from FFR-3M): **SIGNED — warm-start OFF for forecast bundles**

FFR-3M landed 2026-08-04 and adjudicated FF-3E part c as **MECHANISM 2, alternate optima**,
cause confirmed causally (its cell C): `ScenarioConfig.forecast_xyear_warmstart` (default
`True`) warm-starts each year from the prior year's basis; a resumed run has no basis to
inherit, solves that year cold, and lands on a different vertex of a degenerate optimal face.
FFR-3M escalated the trade rather than deciding it. It is now decided.

**Owner decision, 2026-08-04: Option 2 — `forecast_xyear_warmstart=False` for forecast
bundles.** Drill goes green (measured), resume-reproducibility becomes structural, and the
cold answer is also the canonical one, so the reproducible result becomes the default result.
Cost accepted: the ~2.3× steady-state P0 speedup, negligible on a 3-year T0 and material on a
25-year full-horizon T1.

Option 3 (pin a basis) was put with its measured cost and **not** taken — it would freeze one
vertex of a tied optimal face as "the" answer and, because the retirement screen reads
per-unit dispatch volumes, would let a solver setting silently select which marginal units
retire (ERCOT: objective relΔ 8.3e-4, max |Δ zonal price| 0.19 $/MWh). That is the coupling
rule 1 `[R-STRUCT]` exists to prevent.

**Coordination hazard, flagged for the implementing lane (FFR-3T):**
`forecast_xyear_warmstart` is an **included** cache-key field (`scenarios.py` ~L486–493 — the
comment there states `False` "enters the key as a distinct scenario"), so flipping the default
**shifts every forecast cache key**. That is a cache-epoch-scale event and must be declared as
one, sequenced against any in-flight forecast solve lane — FFR-3Q-2 in particular.

### K.4 — dispatch-ledger correction: the pack's Wave-3 ledger was stale within hours

The ledger written at `ee14c4a7` lists FFR-3K, FFR-3M and FFR-3R as **NEVER DISPATCHED**. Two
of the three have since run and merged. Corrected state:

| lane | ledger said | **actual at `145e4c5f`** |
|---|---|---|
| FFR-3M | never dispatched | **LANDED** (`4c403dd9`, PR #3482) — FF-3E part c = alternate optima; produced D-10 |
| FFR-3R | never dispatched | **LANDED** (`0f788c29`, PR #3476) — found **instance five** (hardcoded literals in `register_forecast_baseline.py`), closed the class structurally via `scripts/lib/run_record.py`; proven record-only (`cache_key(ScenarioConfig())` = `603c2498bf71d21d` unchanged, `git diff origin/main -- src/` empty) |
| **FFR-3K** | never dispatched | **STILL NEVER DISPATCHED, defect live at HEAD** — `run_capacity_hindcast.py` **L1419** still `to_yaml_full(... "run_config.yaml")` while FC-7 reads `.json`. (FFR-3Q §3.5 cites L1303; the line has moved, the defect has not.) |

The four lanes now dispatched — **FFR-3K**, **FFR-3Q-2**, **FFR-3S** (D-9(ii)), **FFR-3T**
(D-10) — are written into the prompt pack in the same session, per the standing rule that a
prompt delivered only in chat is a prompt that gets lost.

### K.5 — still open after this addendum

* **D-2′** (`entry_vre_capacity_revenue`) remains **unprobed** — no lane owns it.
* **CAISO FC-2 row 4** still FAILs at **63.23 %**; FFR-3H's cause 2 (a CAISO `gas_ct`
  unprofitable in the entry screen in every year of every arm by $39,974–45,316/MW-yr) is
  diagnosed and **unchartered**. Offered to the owner, not self-chartered.
* **Pre-existing test failures on main** remain unowned.

---

## Addendum L — the rule-22 breach, D-11 signed, FFR-3Q-2 retracted

**Written 2026-08-04 by the workstream manager at `origin/main` `8b920ed6`.** Supersedes
Addendum K where they conflict; K is untouched. **L.3 is a manager error correction — read it
the way J.1 was meant to be read.**

### L.1 — STOP-THE-LINE: a validation-tier year was solved under an active freeze

FFR-3Q resumed after Addendum K was written and executed its Task 1. Both arms of the
base-2021 T1-FF window **solved 2022** — a validation-tier holdout year — under an **ACTIVE**
holdout spend freeze, and **read** measured 2022 demand, renewable CF, forced-outage derate and
hydro. `meta.json`, both arms: `solved_years: [2021, 2022, 2023, 2024, 2025]`,
`bridged_years: []`. Rule 22's bridge contract — *"evolved across, never solved, data never
read"* — is violated in **both** halves. Evidence: `4724fa83`, and
`docs/handoffs/ffr-3q-window-recut-2026-08-04.md` §2.2.

**Cause is a harness defect, not an operator choice.** Two predicates disagree about what a
"forward year" is:

* `runner.is_bridge` un-bridges a bridge year when `config.is_crossover_forward_year(year)`.
  T1-FF's construction points `crossover_forward_year` at the window's **own base year**, so at
  base 2021 *every* year ≥ 2021 is a "crossover forward year" — including 2022 **and 2026**, had
  a window reached it.
* `_validate_window` computes its solve-year set from the **`--crossover` flag** (False for
  T1-FF), so it removed 2022 as a bridge and **never policy-checked it**. The fail-closed check
  never saw the year, because the guard deleted it before the check ran.

The un-bridging clause is correct for a genuine T1-X crossover — forward years 2026/2027, solved
in forecast mode against no measured actuals, which rule 22 permits. Re-pointing the boundary at
2021 silently extended that permission to a year for which it was never true.

**The most dangerous property is the false assurance:** the harness printed a governance banner
promising *"bridges [2022, 2026] are never solved or read"* and then broke it. A future lane
reading that banner would have had no reason to doubt it.

**Why no earlier lane hit it:** every prior T1-FF run — FH-1's gate, all three FFR-3F ERCOT
arms, all three PJM arms — was base 2023 / window 2023–2025, which contains no bridge year. Base
2021 is the first posture whose window contains one, and that posture is precisely what G.5(a)
authorized.

**What the lane did right, and it is worth naming:** it quarantined both bundles
(`QUARANTINE-DO-NOT-REGISTER.txt`), registered nothing, spent no marker, claimed no matrix
verdict, **refused to report the I6/I7/I12 re-probe** on the grounds that a fleet evolved through
a measured-2022 solve is a different experiment, and **did not patch `is_bridge` to make its own
window legal** — the rule-22-adjacent move the policy exists to prevent. It also corrected its
own Task 0 wording unprompted (§2.2.2).

### L.2 — D-11 (NEW): **SIGNED — NO SPEND, conditional on purge and disclosure**

Owner, 2026-08-04. ERCOT's 2022 validation year is **NOT** consumed. The reasoning on record:
rule 22's harm is *tuning against held-out data*, and no number from these arms was ever read —
no scorer ran (scoring is independently bounded to 2023–2025 on both sides), nothing was
registered, no marker file was touched, and the lane refused to quote any derived verdict.

**The determination is only honest if the artifacts genuinely cannot be reused, so it carries
three BINDING conditions, all owned by FFR-3U:**

1. **Delete the two quarantined bundles**, not merely flag them. A `.txt` marker is a convention;
   a deleted bundle is a fact.
2. **Invalidate the two cache keys** `b99600bceb8cb6b8` (arm A) and `5c352508039513da` (arm B).
   Without this, a later run with the same config silently **CACHE-HITS the contaminated 2022
   solve** and inherits the breach with no banner at all. This is the condition that actually
   protects the tier.
3. **Disclose it** on the peer-review §4 standing disclosure list
   (`docs/forecast-readiness-peer-review-2026-07.md`) — not buried in a lane doc.

If any condition cannot be met, D-11 reverts to the strict reading and ERCOT 2022 is spent.

### L.3 — FFR-3Q-2 is RETRACTED, and the manager error that produced it

**The FFR-3Q-2 prompt dispatched earlier today instructs exactly the window that commits this
breach. It is withdrawn. Do not run it.** It is struck in the pack at §0g.

**My error, owned.** Addendum K.1 repeated FFR-3Q's Task 0 as *"VERIFIED by execution"* and the
FFR-3Q-2 prompt told its session *"Do NOT re-derive this and do NOT edit holdout_policy.py."*
Task 0 verified the **guard** — `_validate_window` raises or does not raise. The guard is not
what decides which years get solved; `runner.is_bridge` is. The check that would have caught
this takes about a minute and neither the lane nor I ran it.

This is the J.1 failure mode exactly: a claim about behaviour certified against an artifact
adjacent to the behaviour. J.1 recorded it happening once; L.3 records me doing it again, and
worse — **I hard-coded the unverified claim into a dispatched prompt as a do-not-check
instruction**, which converts my error into an instruction not to find it. A prompt that tells a
session not to re-derive something is only safe when the something was verified at the level the
prompt relies on. Standing correction to my own practice: **a "do not re-derive" clause may only
cover a claim verified at the level of the behaviour the lane will exercise**, and where a
determination certifies a guard rather than a runtime, the prompt says which.

### L.4 — FFR-3U chartered: fix the bridge/un-bridge seam

Dispatched in pack §0g. It carries FFR-3Q §2.2.4's four successor items plus D-11's three
conditions. **It BLOCKS G.5(a)'s gate re-cut, and therefore FH-4/FH-5, which remain blocked.**
FH-4/FH-5 is now blocked for a stronger reason than in K.1: not merely that the re-probe is
unreported, but that the posture it must run on **cannot legally be solved** until the seam is
fixed. §2.1's pre-registration survives intact and is reused verbatim once FFR-3U lands.

Note for whoever eventually re-runs it: the same defect would un-bridge **2026** — a
locked-test year — for any window that reached it. Nothing has reached one; the fix must close
both.

### L.5 — dispatch state after this addendum

| lane | state |
|---|---|
| **FFR-3K** (FC-7) | **UNAFFECTED — run it.** Defect still live at `run_capacity_hindcast.py` L1419 |
| **FFR-3S** (D-9(ii)) | **UNAFFECTED — run it.** Scorer-side, touches no window |
| **FFR-3T** (D-10) | **HOLD RELEASED — run it.** Its hold existed only because FFR-3Q-2 was solving on the old cache key; with 3Q-2 retracted no forecast solve lane is in flight, and landing the flip now means FFR-3U's eventual re-probe runs on the settled posture |
| **FFR-3Q-2** | **RETRACTED** (L.3) |
| **FFR-3U** (seam fix) | **NEW, dispatched** — gates the gate re-cut and FH-4/FH-5 |

Unchanged from K.5: **D-2′** unprobed; **CAISO FC-2 row 4** at 63.23 % with FFR-3H cause 2
diagnosed and unchartered; pre-existing test failures on main unowned.

---

## Addendum M — Wave-3 instrument lanes closed; three new lanes chartered

**Written 2026-08-04 by the workstream manager at `origin/main` `bf43122e`.** Ledger update and
new charters; supersedes K.4/L.5 status lines only.

### M.1 — three dispatched lanes LANDED, one never started

| lane | state |
|---|---|
| **FFR-3K** (FC-7) | **LANDED** PR #3502. `run_capacity_hindcast.py` emits `run_config.json`; the `.yaml` kept because something reads it. Solve-inert, census + inertness proof committed. **K.4's "still never dispatched" line is hereby retired** — FFR-3K's own handoff §6 correctly left this edit to the manager |
| **FFR-3S** (D-9(ii)) | **LANDED** PR #3501. Additions scored on the DECISION basis; `additions_basis` recorded in `score.json` via FFR-3R's `RecordSpec`; `additions_cod_basis` kept for within-run comparison only and is **not** the graded instrument |
| **FFR-3T** (D-10) | **LANDED** PRs #3498/#3504. Took the **forecast-path override**, not a default flip — `scenarios.py` still ships `forecast_xyear_warmstart: bool = True` with `scripts/lib/forecast_posture.shipped_forecast_xyear_warmstart` as the single source, so backcast solves are untouched and the decision was not exceeded. Cache epoch **2026-08-04** declared; handoff + key census landed |
| **FFR-3U** (bridge seam) | **NEVER STARTED.** No branch, no doc. Seam confirmed open at `runner.py:927` |

**FFR-3U's not starting has a live consequence, restated because it is easy to lose:** D-11's
no-spend determination for ERCOT 2022 is **conditional and undischarged**. Cache keys
`b99600bceb8cb6b8` / `5c352508039513da` have not been invalidated by anyone. Until they are, a
run with that config can silently cache-hit the contaminated 2022 solve. FH-4/FH-5 remains
blocked behind the same lane.

### M.2 — the entry screen is now the program's largest open finding, in TWO ISOs

Two lanes independently landed on the same *shape* of defect in different markets. **Rule 25
`[R-ISO-SCOPE]` binds absolutely: these are two lanes, not one, and neither may import the
other's verdict, parameters, or diagnosis.** They are recorded together only so the manager
ledger does not pretend they are unrelated in kind.

* **MISO — FFR-3S §6.** `miso-2021-2025-realized-ffr3a3` fails FC-3 additions on all five techs,
  most starkly **solar: model 0.0 GW vs actual 18.649 GW (−100 %)**. FFR-3S showed the new
  decision basis **cannot** explain it: with a 2-year lag and a 2021 start, the 2021/2022/2023
  cohorts commission in 2023/2024/2025 — **inside** the window and already visible under the COD
  basis — so those three cohorts decided **zero** solar. Only 2024/2025 were censored. Three
  cohorts of zero solar in the ISO that actually added 18.6 GW is an **entry-screen root cause**
  (rules 1/11/14), not a scoring artifact. Chartered as **FFR-3V**.
* **CAISO — FFR-3H cause 2.** A CAISO `gas_ct` is unprofitable in the entry screen in **every
  year of every arm** by **$39,974–45,316/MW-yr**, and FC-2 row 4 still FAILs at **63.23 %**
  (FFR-3P's identified VRE accreditation moved it from 65.48 %, with zero invariant flips).
  Diagnosed and unowned since Addendum J. Chartered as **FFR-3W**.

Both are **diagnosis** lanes. Neither may tune a parameter to close its residual; a residual
closable only by an unidentified value is an open blocker to be written up (rule 11).

### M.3 — FFR-3X: the record-provenance follow-up FFR-3K identified

`scripts/_ff2d_emit_run_config.py` will **silently overwrite a producer-written
`run_config.json` with a `meta.json`-reconstructed one** if run on a post-FFR-3K bundle — a
provenance downgrade, and precisely the defect class FFR-3R closed structurally. Its hindcast
arm also still reads `meta.json` rather than `run_config.yaml` (FFR-3R §6.1, open). FFR-3K
scoped it out correctly and named the remedy: a refuse-if-exists guard. Small lane.

### M.4 — carried forward, still unowned

**D-2′** (`entry_vre_capacity_revenue`) unprobed — note it is now adjacent to M.2's finding and
a successor may want it sequenced after FFR-3V/FFR-3W rather than before. Pre-existing test
failures on main unowned.

---

## Addendum N — Wave 3 lanes all closed; D-11 discharged; the open decision register

**Written 2026-08-04 by the workstream manager at `origin/main` `a9df3b99`.** Records landed
facts only; the decisions in N.5 are OPEN and unsigned.

### N.1 — every lane chartered in Addenda K/L/M has LANDED

| lane | PR | outcome |
|---|---|---|
| **FFR-3K** | #3502 | FC-7 fixed. `run_capacity_hindcast.py` emits `run_config.json` from the bundle's OWN resolved config; the `.yaml` kept because something reads it. Census + inertness proof committed |
| **FFR-3S** | #3501 | D-9(ii) landed — additions scored on the DECISION basis, `additions_basis` recorded via FFR-3R's `RecordSpec` |
| **FFR-3T** | #3498/#3504 | D-10 landed as a FORECAST-PATH OVERRIDE, not a default flip; backcast untouched; cache epoch 2026-08-04 declared |
| **FFR-3U** | #3526 | The seam is FIXED and **D-11 is fully DISCHARGED** — see N.2 |
| **FFR-3V** | #3527/#3528/#3530 | MISO solar diagnosed: a MARGIN finding. Five ranked proposals, none applied — see N.4 |
| **FFR-3W** | #3519 | CAISO gas_ct decomposed; the verdict is real, the magnitude is a defect, and the obvious fix is a rule-1 trap — see N.3 |
| **FFR-3X** | #3518 | Refuse-if-exists guard landed; FFR-3R §6.1 closed |

### N.2 — FFR-3U: the seam is closed and **ERCOT 2022 STAYS UNSPENT**

The un-bridging clause is **scoped, not deleted**: at base 2021 the runner again bridges 2022
(validation) and 2026 (locked test), and the illegal window now FAILS CLOSED. Three predicates
became one — `_validate_window` policy-checks the set the **runner** will actually solve, via
the runner's own predicate over the boundary `build_config` sets. The banner's promise is
derived from that same predicate and **asserted against the realized evolution ledgers at
completion**; a mismatch is a hard `SystemExit`.

**D-11's three conditions (Addendum L.2): (a) DISCHARGED by verified absence, (b) DISCHARGED
mechanically, (c) DISCHARGED.** Condition (b) — the one identified as protecting the tier — was
discharged **better than chartered**: a refusal in code at the single cache-path seam rather
than a ledger note, so `b99600bceb8cb6b8` / `5c352508039513da` cannot be cache-hit at all.
**The no-spend determination therefore stands and ERCOT's 2022 validation year remains
available** once properly authorized.

**Exposure audit: 0 affected artifacts, as a MEASUREMENT** — all **82** committed
hindcast-harness legs replayed through the fixed predicate using each leg's own recorded window
and boundary. FFR-3Q §2.2.4 asked for this precisely because the nil result had been *reasoned*
rather than measured. Solve-inert: seven cache keys byte-identical, no keeper moved. One finding
reported rather than a threshold relaxed: the FC-7 fixture was asserting a solve-year set
inconsistent with its own declared window; the fixture was made honest and the new parity
assertion was **not** weakened.

**Consequence for FH-4/FH-5: the blocker has CHANGED, not cleared.** It is no longer "the
posture cannot legally be solved" — it is again "the re-probe is unreported". The gate re-cut is
now legal to run and FFR-3Q §2.1's pre-registration is reusable verbatim. The lift remains a
manager box (Addendum I.1).

### N.3 — FFR-3W: the CAISO fix that would have been a rule-1 trap

1. **The `unprofitable` verdict is a REAL market signal.** A new merchant CT breaks even at
   **$10.88–11.36/kW-month** against CAISO's published transacted RA price of
   **$11.10–14.51/kW-month**, in a market **6.9 % long** on RA.
2. **The $40 k magnitude IS a defect, and ~100 % one term.** ≥94 % of the gap in every year is
   the capacity-price anchor — the CPM soft-offer cap, whose own FERC provenance is the
   *going-forward fixed cost of a 550 MW **CC** reference unit × 1.20*: a **retention** cost for
   an existing combined-cycle used as the **entry** price for a new combustion turbine. Energy,
   AS and the cost stack are ≤27 % of the gap in the best year and ≤0.1 % in the worst.
3. **Fixing it would turn FC-2 row 4 green FOR THE WRONG REASON.** Row 4's real driver is a
   base-year fleet **11,711 MW short** of the real CAISO (FFR-3P Table 1.1) — **1.78×** the
   6,577 MW deficit driving the whole 14,043.6 MW build. Correcting the `gas_ct` term moves row
   4 just as far by building *the same 14 GW of CTs California does not need*, through the
   economic channel instead of the administrative one. **Row 4 would read PASS while the model
   still over-builds 14 GW into a long market** — the right number through a mechanism that
   isn't real, which is rule 1 `[R-STRUCT]` exactly.

**FFR-3W's recommendation, unmodified: do NOT charter the capacity-anchor correction as a row-4
fix.** If chartered at all it stands on its own rule-14 merits, and row 4 is chartered against
the fleet-vintage cause (FFR-3P **B-1**).

### N.4 — FFR-3V: MISO solar is a margin finding, plus a structural knife-edge

**It is a MARGIN finding — not candidate-set, not damper.** Solar reaches the screen every
decision year; the per-tech queue cap (6.0 GW) and growth-ladder cap (1.236 GW) are both
non-zero; it is rejected on economics *before* any cap is consulted. The internal control is
decisive: **wind built 4.0 GW in the same window through the same code path, the same zonal-CF
mechanism and the same caps.** The distinction this lane was chartered to draw was drawn, twice.

Solar's only revenue is merchant energy (~$60–75 k/MW-yr) against $84.8–99.0 k/MW-yr annualized
fixed. RPS is **structurally zero** (MISO's 11 % target is slack against a 16.9 % modelled VRE
share). **`entry_vre_capacity_revenue` is default-OFF and would be worth $14,364/MW-yr** — and
the thermal branch already takes the same payment **ungated** at $75.8 k–117.3 k/MW-yr, so the
asymmetry sits inside one function.

**The second, independent blocker — and it is structural.** With a COD lag of `L`, `(L−1)` years
of decisions are pending when the screen runs, so `remaining = (K − L + 1) × D_prev`. **At the
shipped `K = 2.0` and `L = 2` that is exactly `1 × D_prev`: the doubling and the pending netting
cancel EXACTLY, and economic entry is pinned at 2× the measured seed forever.** The knife-edge
is `K = L` and the shipped values sit on it. MISO solar's ceiling is therefore **2.473 GW
in-window — a −86.7 % FC-3 band at best, even with a perfect revenue side.** Removing only the
lag lifts it to 14.655 GW (−21.4 %), at which point the 6.0 GW queue cap binds instead.

This reconciles with FFR-2B's observation that MISO's gas_ct ladder *did* double
(1,350 → 2,700 → 5,241 MW): that is the **reserve-margin backstop**, which commissions **in-year**
and so never nets a pending row. **The same ladder ratchets for the backstop and freezes for
economic entry.** Nothing was unarmed and no revert is recommended (Addendum D holds).

### N.5 — OPEN DECISION REGISTER (unsigned; do not read any of these as taken)

* **D-2′ — arm `entry_vre_capacity_revenue`?** HELD since Addendum C "pending its own probe
  row". **The probe row now exists** (FFR-3V §7 proposal 1). Note its size is decided by the
  next item, so the two should be considered together.
* **D-12 — wire MISO's published solar accreditation** from the already-intaken
  `elcc/miso/miso.csv` into `RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]`, and settle the
  seasonal→annual selection rule. Rule 14: the accurate value is **on disk and cited**. Unwired
  0.18 moves solar's 2023 break-even to $37.59; the season-weighted 0.3875 moves it to $29.41.
* **D-13 — window the §45 wind PTC to its statutory 10 years.** Zero free parameters, one
  published number, and an existing precedent in the same file (`_ccs_45q_window_years`).
  **Expect wind additions to FALL** — under rule 1 that is the faithful direction, not a
  regression, and it must not be judged by whether the band improves.
* **D-14 — is the `K = L` ladder freeze a defect or intended conservatism?** Owner call. Even
  with D-2′/D-12/D-13 all taken, FC-3 solar cannot clear −15 % while the ceiling is ~3.7 GW.
* **D-15 — the CAISO capacity anchor.** Take FFR-3W's recommendation (N.3) or overrule it.
* **The FH-1 gate re-probe** needs re-dispatching now that FFR-3U has landed.

Lower-ranked and unowned from FFR-3V §7: the VRE screen's siting-zone CF (proposal 3, needs its
own derivation) and the hindcast renewable-pool vintage leak (proposal 4 — a one-line gate
widening that changes every hindcast's base fleet, so it belongs to whoever owns the T1-H lane).
Carried forward: pre-existing test failures on main remain unowned.

---

## Addendum N-cards — the six open decisions, as sign-off cards

**Written 2026-08-04 by the workstream manager at `origin/main` `a9df3b99`.** These are the
N.5 register entries in card form. **Take them in the order given** — D-14 changes what D-12
and D-2′ are worth, and D-12 sizes D-2′.

---

### CARD D-14 — Is the entry growth ladder's `K = L` freeze a defect or intended conservatism?

**TAKE THIS FIRST.** It determines what every other MISO entry decision is worth.

**Measured.** The ladder lets year *Y* build `K ×` the prior year's decisions, then nets off
decisions already pending. With a COD lag of `L` years, `(L−1)` cohorts are always pending when
the screen runs, so `remaining = (K − L + 1) × D_prev`. **At the shipped `K = 2.0` and `L = 2`
that is exactly `1 × D_prev`** — the doubling and the netting cancel *exactly*, and economic
entry is pinned at 2× the measured seed forever. The knife-edge is `K = L`; the shipped values
sit on it. MISO solar's ceiling is **2.473 GW in-window = a −86.7 % FC-3 band at best, even with
a perfect revenue side.** Removing only the lag lifts it to 14.655 GW (−21.4 %), at which point
the 6.0 GW per-tech queue cap binds instead. Corroboration: MISO's gas_ct ladder *does* double
(1,350 → 2,700 → 5,241 MW, FFR-2B) — but that is the reserve-margin **backstop**, which
commissions **in-year** and so never nets a pending row. **The same ladder ratchets for the
backstop and freezes for economic entry.**

**Recommendation: (a) CHARTER IT AS A DEFECT**, on the grounds that a cancellation this exact is
an accident of two independently-chosen parameters, not a designed conservatism — and that a
mechanism which ratchets in one channel and freezes in another is one mechanism doing two things
(rule 19 `[R-ONE-MECH]`). Charter a lane to derive the intended relationship between `K` and `L`
from the measured build record; **do not simply move `K` off 2.0** — that is tuning a knife-edge
to taste.

**The option I think is wrong, with its real cost: (b) ACCEPT IT AS INTENDED.** Cheap today, and
defensible as "the model should not out-build the historical record." The cost is that
**FC-3 additions can never pass in MISO** — the ceiling is ~3.7 GW against 18.649 GW actual — so
the band stops being an instrument and becomes a permanent known-fail. You would also be
accepting that D-2's entry-side skill is unmeasurable in this ISO, which is the same predicament
D-9 was re-opened over.

**Sign-off D-14:** ☐ (a) charter as defect  ☐ (b) accept as intended  ☐ other: ____________
owner: ________  date: ____

---

### CARD D-12 + D-2′ — MISO's solar revenue side. **One decision, two parts.**

They are paired because **D-12 sizes D-2′**: the accreditation value is the multiplier on the
capacity payment D-2′ switches on. Deciding D-2′ alone would be picking a number before knowing
which number it is.

**D-12 — wire MISO's published solar accreditation.** The rows are **already intaken and cited**
at `elcc/miso/miso.csv` and are simply not read into
`RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]`. Unwired the model uses **0.18**; the season-weighted
published value is **0.3875**. Effect on solar's 2023 break-even: **$37.59/MWh at 0.18 vs
$29.41/MWh at 0.3875**, against a MISO modelled price level of ~$30–40/MWh — i.e. the wiring
decides whether solar clears at all. Rule 14 `[R-ACCURATE]`: the accurate value is on disk.
Wiring it also forces a seasonal→annual selection rule, which must be settled in the same lane
rather than left implicit.

**D-2′ — arm `entry_vre_capacity_revenue`.** HELD since Addendum C "pending its own probe row";
**the probe row now exists.** The payment resolves cleanly today ($79,800 × 0.18 =
**$14,364/MW-yr**) and moves solar's break-even from $41.9–48.9 to **$34.8–41.8/MWh**. The
decisive asymmetry: **the thermal branch already takes the same payment UNGATED at
$75.8 k–117.3 k/MW-yr** — VRE is gated off and thermal is not, inside one function.

**Recommendation: take BOTH, D-12 first, in one lane, with a paired control.** D-12 is a rule-14
obligation independent of its effect. D-2′ then becomes a correction of an asymmetry rather than
a new mechanism. Scope it to MISO and re-examine other ISOs where `MARKET_DESIGN` has a capacity
market **as separate per-ISO decisions** (rule 25 `[R-ISO-SCOPE]` — no cross-ISO transfer).

**The option I think is wrong, with its real cost: arm D-2′ alone and leave D-12 unwired.** It
looks like the cautious half-step, and it is the worst of both: you switch on a capacity payment
sized by an **estimate the ISO has already published a better number for**, so the resulting
build is an artifact of the wrong multiplier — and if the fit improves, rule 14's warning applies
in full, because an inaccurate input would be silently compensating for something.

**Note before signing:** if D-14 goes (b), this pair moves MISO solar from a −100 % band to
−86.7 %. Still FAIL. It is worth doing on rule-14 grounds regardless, but it will not buy a pass.

**Sign-off D-12:** ☐ wire it  ☐ leave unwired  ☐ other: ____________
**Sign-off D-2′:** ☐ arm (MISO-scoped)  ☐ hold  ☐ other: ____________
owner: ________  date: ____

---

### CARD D-13 — Window the §45 wind PTC to its statutory 10 years

**Measured.** The wind PTC is credited over the plant's **full 30-year book life** with no
statutory window; the solar ITC in the same file is booked correctly. The remedy has **zero free
parameters** — one published statutory number (10 years) — and an existing precedent to copy in
the same file (`_ccs_45q_window_years`).

**Recommendation: TAKE IT.** This is a straightforward correctness fix under rule 5
`[R-NO-MAGIC]` and rule 14, not a calibration lever.

**Read this before signing, because it is the part that gets mis-handled: EXPECT WIND ADDITIONS
TO FALL.** MISO's leg currently builds 4.0 GW of wind against 7.2 GW actual, so the correction
moves a passing-ish number *further from* the actual. **Under rule 1 `[R-STRUCT]` that is the
faithful direction and the fix stays in.** If the band worsens, that is a discovered
under-build elsewhere on wind's revenue side — an open root cause to write up, **not** a reason
to revert. A lane that reverts this because the residual moved has misread the rule.

**The option I think is wrong, with its real cost: defer it until the revenue side is fixed, so
the two land together and the band never visibly worsens.** That is exactly the reasoning rule 1
forbids — sequencing a correctness fix around its effect on a fit — and it would leave a
30-year credit on a 10-year statute in the shipped model in the meantime.

**Sign-off D-13:** ☐ take it now  ☐ defer  ☐ other: ____________
owner: ________  date: ____

---

### CARD D-15 — The CAISO capacity anchor, and what may NOT be chartered against FC-2 row 4

**Measured (FFR-3W).** The `unprofitable` **verdict is a real market signal** — a new merchant CT
breaks even at $10.88–11.36/kW-month against CAISO's published transacted RA price of
$11.10–14.51/kW-month, in a market **6.9 % long** on RA. But the **$40 k magnitude is a defect
and ~100 % one term**: ≥94 % of the gap in every year is the capacity-price anchor, the CPM
soft-offer cap, whose own FERC provenance is *"the going-forward fixed cost of a 550 MW **CC**
reference unit × 1.20"* — a **retention** cost for an existing combined-cycle used as the
**entry** price for a new combustion turbine. Energy, AS and the cost stack together are ≤27 % of
the gap in the best year and ≤0.1 % in the worst.

**The trap, and it is the decision.** Row 4's actual driver is a base-year fleet **11,711 MW
short** of the real CAISO — **1.78×** the 6,577 MW deficit that drives the entire 14,043.6 MW
build. Correcting the fleet alone moves the reserve position 0.8852 → 1.0896 (11.5 % short →
9.0 % long) and collapses row 4's numerator. **Correcting the `gas_ct` anchor instead moves row 4
just as far — by building the same 14 GW of CTs California does not need, through the economic
channel rather than the administrative one. Row 4 would read PASS while the model still
over-builds 14 GW of firm capacity into a market that is already long.**

**Recommendation: (a) ADOPT FFR-3W's RECOMMENDATION UNMODIFIED.** Charter FC-2 row 4 against the
**fleet-vintage** cause (FFR-3P **B-1**). The anchor correction may be chartered *separately*, on
its own rule-14 merits as a mis-specified published input, and **its charter must state that it
is not a row-4 fix** so no later session quotes a row-4 improvement as its justification.

**The option I think is wrong, with its real cost: (b) charter the anchor correction as the row-4
fix** — one lane, one obviously-wrong input, row 4 goes green. The cost is that you would be
buying the right number through a mechanism that isn't real, which is rule 1 `[R-STRUCT]`
verbatim, and you would **lose the signal**: with row 4 green, the 11,711 MW fleet shortfall
stops being visible in any gate and survives into the forecast.

**Sign-off D-15:** ☐ (a) fleet-vintage cause; anchor separate and labelled  ☐ (b) anchor as the
row-4 fix  ☐ other: ____________
owner: ________  date: ____

---

### CARD — Re-dispatch the FH-1 §3.3 gate re-probe

Not a design decision; a go/no-go on spending a lane. **FFR-3U has landed**, so the base-2021
T1-FF window is now legal and fails closed where it should. FFR-3Q §2.1's pre-registration
survives verbatim and is reusable — posture, pairing (arms A `pipeline` / B `legacy`), and all
four pre-registered reads. What is still unknown is the thing the re-cut was authorized to find
out: **whether the 2021/2022 screens produce any exit candidates at all**, or whether
`pipeline_events` is zero a third time.

**Recommendation: dispatch it.** Both prior probes were uninformative for the same reason and
G.5(a) was signed specifically to make the retirement layer observable; leaving it unexercised
means D-1 stays unvalidated on the exit side indefinitely. **The lift itself remains a manager
box** (Addendum I.1) and the reading is bound by Addendum G.2's three constraints — the earlier
green was not the fix's, I12's WARN had inverted sign, and zero `pipeline_events` means UNTESTED,
not validated.

**Sign-off:** ☐ dispatch now  ☐ hold  ☐ other: ____________
owner: ________  date: ____

---

## Addendum O — the five N-cards are SIGNED; Wave 4 opens

**Written 2026-08-04 by the workstream manager.** Owner signed all five N-cards on 2026-08-04,
each on the stated recommendation. Wave 3 is closed (Addendum N.1); these charters open Wave 4.

### O.1 — the signatures

| decision | signed | what it authorizes |
|---|---|---|
| **D-14** | **CHARTER AS A DEFECT** | A lane to derive the intended relationship between the ladder multiplier `K` and the COD lag `L` **from the measured build record**. Explicitly **NOT** a licence to move `K` off 2.0 — tuning a knife-edge to taste is the thing the card refused |
| **D-12** | **WIRE IT** | MISO's published solar accreditation read into `RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]` from the already-intaken `elcc/miso/miso.csv`, seasonal→annual selection rule settled in the same lane |
| **D-2′** | **ARM (MISO-scoped)** | `entry_vre_capacity_revenue` armed, **after** D-12 and in the same lane, with a paired control. Other capacity-market ISOs remain **separate per-ISO decisions** (rule 25) |
| **D-13** | **TAKE IT NOW** | The §45 wind PTC windowed to its statutory 10 years, on the existing `_ccs_45q_window_years` pattern |
| **D-15** | **FLEET-VINTAGE; ANCHOR SEPARATE** | FC-2 row 4 chartered against the fleet-vintage cause (FFR-3P **B-1**). The CAISO capacity-anchor correction is **NOT chartered by this decision** — it may be chartered later on its own rule-14 merits, and any such charter must state it is not a row-4 fix |
| **re-probe** | **DISPATCH NOW** | The FH-1 §3.3 gate re-probe, on FFR-3Q §2.1's surviving pre-registration |

### O.2 — the consequences the owner accepted, recorded once so no lane re-opens them

* **D-13 will make wind additions FALL** (MISO builds 4.0 GW against 7.2 GW actual). That is the
  faithful direction under rule 1 `[R-STRUCT]`; a worse band is a discovered under-build on
  wind's revenue side, to be **written up as an open root cause and never reverted**. A lane that
  reverts D-13 because the residual moved has misread the decision.
* **D-12 + D-2′ will not buy an FC-3 pass on their own.** If the ladder freeze survives D-14's
  derivation, they move MISO solar from a −100 % band to −86.7 %. They were taken on rule-14
  grounds, not on expected band movement, and must not be judged by it.
* **D-15 deliberately declines the cheaper green.** Correcting the CAISO anchor would move row 4
  just as far by building the same 14 GW of CTs California does not need. Row 4 is chartered
  against the 11,711 MW fleet shortfall instead, so that shortfall stays visible in the gates.
* **The re-probe's lift remains a MANAGER box** (Addendum I.1). The lane reports; it does not
  lift, and reporting green does not lift.

### O.3 — Wave 4 lanes, dispatched in pack §0i

| lane | decision | model | notes |
|---|---|---|---|
| **FFR-4A** | D-14 | OPUS | Derive `K`/`L` from the measured record. **Rule 23 `[R-FROZEN-DERIVE]` binds hardest here** |
| **FFR-4B** | D-12 + D-2′ | OPUS | One lane, D-12 first, paired control. New/changed `ScenarioConfig` behaviour ⇒ rule 28 matrix duty |
| **FFR-4C** | D-13 | FABLE | Bounded; zero free parameters; precedent in the same file |
| **FFR-4D** | D-15 | OPUS | CAISO row 4 against fleet vintage (FFR-3P B-1) |
| **FFR-3Q-3** | re-probe | OPUS | Finishes FFR-3Q Task 1; keeps the 3Q lineage and its pre-registration |

**Concurrency (rule 12 per prompt, Addendum F.2): all five may run as independent sessions.**
One coupling to manage: **FFR-4B and FFR-4C both touch entry-screen revenue in MISO** — 4B raises
solar, 4C lowers wind. Each must therefore carry **its own paired control against the shipped
default at its own base commit**, and whichever lands second re-verifies against the new base.
Without that, MISO's FC-3 moves on two axes at once and neither change has a clean attribution.
They also risk a merge race on the mechanism matrix (miso-124 lost one); second-in re-checks its
cell survived.

**Not chartered by anything here:** the CAISO capacity-anchor correction (D-15 explicitly), the
VRE screen's siting-zone CF (FFR-3V proposal 3), the hindcast renewable-pool vintage leak
(proposal 4 — belongs to whoever owns the T1-H lane), and the pre-existing test failures on main.

---

## Addendum P — CORRECTION: FFR-3V re-measured after the N-cards were signed

**Written 2026-08-04 by the workstream manager at `origin/main` `c7d806eb`.** Corrects the
evidence block of the **D-12 + D-2′ card** in Addendum N-cards. **No signed decision is
reversed**, but the number the owner was shown is superseded and the *ranking* has changed.
Read this as the same class of act as J.1 and L.3.

### P.1 — what I told the owner, and what the measurement actually says

The N-card quoted the MISO capacity payment as **"$79,800 × 0.18 = $14,364/MW-yr"**. FFR-3V
reopened after the cards were written (`b920be45` "run complete (exit 0) — 2025 lands and
REVERSES the §3.3 correction", `489f0661` "correct the §0 headline table to the measured RA zero
and margin") and measured it properly across all four decision years. **The payment is not a
single standing number. It is zero for three years and very large in the fourth:**

| decision year | MISO reserve margin | capacity payment, ALL techs | solar margin $/MW-yr |
|---|---|---|---|
| 2022 | 27.3 % | **$0** | −26,446 |
| 2023 | 20.7 % | **$0** | −22,681 |
| 2024 | 11.4 % | **$0** | −35,946 |
| **2025** | 17.3 % | **$327,456/MW-yr firm** | −33,406 |

MISO is **long** through 2024 and its VRR pays nothing above a ~1.02 position — **that is
faithful, not broken** (the real PY2021-22 PRA cleared at ≈$1,825/MW-yr). In 2025 the payment
switches on and is *the entire reason* gas CC and CT flip profitable and build 4.48 GW.

**The correction makes D-2′'s case SHARPER, not weaker.** In 2025 the ungated **thermal** branch
takes **$307–311 k/MW-yr** while solar is denied its share by a default-off gate; crediting even
the stingy generic 0.18 fallback gives solar **$58,942/MW-yr**, flipping its margin from
−$33,406 to **+$25,536**. The mechanism is **inert while the ISO is long and decisive the moment
it tightens** — which is a better characterisation than the flat annual figure I gave.

### P.2 — two things the owner did not have when signing D-12 + D-2′

Neither reverses the decision. Both must travel with it.

1. **Arming D-2′ would NOT have moved this leg's FC-3 band at all.** A 2025 decision commissions
   at COD 2027 — outside the 2021–2025 window. Addendum O.2 already recorded "will not buy an
   FC-3 pass"; the measured reason is sharper than the reason I gave.
2. **The ranking inverted.** FFR-3V now ranks **arming D-2′ as 1a** and **wiring the
   accreditation as 1b, SUBORDINATE to it** — because the accreditation "only bites where the
   payment is non-zero", i.e. in 2025 alone on this record. My card's framing ("D-12 sizes
   D-2′") is true only where the payment is non-zero, which is one year in four. **The lane
   order in FFR-4B is therefore amended: arm-then-wire is acceptable, and the two must still
   land in one lane with separable measurement.**

### P.3 — TWO CAUSES FFR-3V FOUND THAT OUTRANK EVERY REVENUE LEVER

Both were measured after the cards were signed. **Neither is chartered by any signed decision.**

**(a) The procurement channel is missing entirely — FFR-3V's own #1, and it is a MISSING
MECHANISM, not a mis-set value.** Both revenue levers the screen *could* be given are correctly
≈zero in MISO over this window (PRA ≈$1,825/MW-yr; the 11 % RPS slack). **Yet 18.6 GW was
built** — on utility IRP/RFP procurement and corporate PPAs against the ITC, a long-term
contracting channel with **no representation anywhere in `apply_economic_new_entry`, which
screens merchant energy margin only.** FFR-3V states the rule-1 reading explicitly: *closing this
by tuning a revenue adder until solar clears would be exactly the fitted-adder failure rule 1
forbids.* No parameter fixes it. **This is an owner decision, not a manager charter** — it is a
new mechanism. Put as card D-16 below.

**(b) The 2024 entry price signal has no ORDC tail at all, and it is upstream of everything.**
`scarcity_price_overlay: False` leaves the lookahead stack with **a maximum hourly price of
$39/MWh** against solar's $43.18/MWh break-even *mean* — the margin is not close, it is
**unreachable**. It also zeroes the peaker outright (`gas_ct` variable cost $41.39 > the $39
ceiling). FFR-3V calls it *"the largest single suppressor of MISO entry in 2024/2025 — upstream
of every revenue lever below."* This one is a **diagnosis** lane and I have chartered it as
**FFR-4E** (pack §0j) without an owner card, because it investigates whether an existing overlay
is wrongly off in the lookahead stack rather than proposing a new mechanism. If it turns out to
require a new mechanism, it escalates.

### P.4 — D-13 is STRENGTHENED by the re-measurement

FFR-3V now quantifies it: the screen credits wind **$86,549/MW-yr** and solar
**$26,787–32,873/MW-yr**, and names this **the mechanical origin of the leg's inverted tech mix**
— model wind share 43.7 % / solar 0.0 % against actual 22.5 % / 58.3 %. The signed decision is
unchanged and better supported. FFR-4C's evidence block is updated accordingly.

### P.5 — unaffected by this correction

**D-14** (the ladder knife-edge) — the §5 finding is intact and unchanged. **D-15** (CAISO) and
the **re-probe** — different ISOs/lanes entirely. FFR-4A, FFR-4C, FFR-4D and FFR-3Q-3 dispatch as
written; only **FFR-4B**'s evidence block and lane order are amended (pack §0j).

### P.6 — also landed, and both matter to the ledger

* **CAISO's `complete` assessment REVERSED to YES** (`0043fc22`). The owner restated the
  criterion — `complete` means exactly (a) the 2022 touchpoint is allowed and (b) frontier, i.e.
  everything testable has been tested. **It is not a certificate that the DOF ledger is clean.**
  caiso-171's prior NO rested on "the active freeze makes the grant hollow", which the record
  refutes: the freeze was declared 2026-07-25 and **NYISO and PJM were both declared complete on
  2026-07-31, six days into it.** `holdout-freeze.json` says so itself — a freeze is *"a
  SUSPENSION of the authorization that a calibration-complete marker grants, not a withdrawal of
  the marker itself."* **The marker and the freeze are orthogonal.** Any session reasoning that a
  freeze blocks a marker has the relationship backwards.
* **NYISO's keeper moved again → `2026-08-04-nyiso-125-seam-envelope`.** That is the **eighth**
  NYISO keeper in five days.

---

### CARD D-16 — Represent the procurement channel that actually built MISO's solar?

**Measured (FFR-3V §3.1, §7 proposal 1).** The screen's two available revenue levers are
*correctly* ≈zero in MISO over 2021–2025 — the PRA cleared ≈$1,825/MW-yr and the 11 % RPS is
slack against a 16.9 % modelled VRE share. **18.649 GW of solar was built anyway**, on utility
IRP/RFP procurement and corporate PPAs against the ITC. `apply_economic_new_entry` screens
**merchant energy margin only** and represents that channel **nowhere**. No parameter fixes it;
FFR-3V declined to propose one and named the gap instead.

**Recommendation: (a) CHARTER IT AS A STRUCTURAL LANE — scoping first, no implementation.** A
lane that specifies what the mechanism would have to be (what drives procurement volume, how it
regenerates in a forecast year, what data identifies it) and returns a design + a rule-13
`[R-MEASURED]` admissibility argument **before** any code. Rule 1 `[R-STRUCT]` says get the
structure right and calibrate after; this is the structure.

**The option I think is wrong, with its real cost: (b) LEAVE IT AS A DISCLOSED LIMITATION** and
proceed on the revenue levers. Cheap, and defensible short-term. The cost is that **MISO's FC-3
additions can never be right for the right reason** — the model would be asked to reproduce an
18.6 GW build through a merchant screen that structurally cannot see why it happened, and every
future lane that tries will be pushed toward the fitted revenue adder rule 1 forbids. You would
also be shipping a forecast whose VRE build in every capacity-market ISO rests on a channel it
does not model.

**Sign-off D-16:** ☐ (a) charter structural scoping lane  ☐ (b) disclosed limitation
☐ other: ____________   owner: ________  date: ____

---

## Addendum Q — Wave 4 closed; the FH-4/FH-5 lift call; the keeper-churn standing instruction

**Written 2026-08-04 by the workstream manager at `origin/main` `0d858b15`.**

### Q.1 — FH-4/FH-5: **NOT LIFTED.** Manager determination, third time, new reason.

FFR-3Q-3 delivered. **The FFR-3U fix HELD in a real run** — both arms realized
`solved [2021, 2023, 2024, 2025], bridged [2022]`, no `year_2022.parquet`, zero 2022 measured
reads, no parity failure. The breach does not recur.

**And the re-cut achieved its stated purpose:** the retirement layer is OBSERVABLE for the first
time. Arm A carries **1,205 `pipeline_events`** — a 29-unit / 8,218 MW coal cohort decided,
re-confirmed, then reversed — so the headline-finding-by-vacancy branch **does not fire**. G.5(a)
was worth signing.

**But the lift fails on its own terms.** `executed` events are **0**, in every year, in both
arms: the cohort is reversed by the soft latch at 2024, its own `execute_year`. **The EXIT half
of the layer is still untested** — now for a sharper reason than vacancy. Arm A reads
**I6 PASS / I7 PASS / I12 FAIL**; the control reads I6 FAIL / I7 FAIL / I12 WARN, reproducing the
FH-1 §3.3 triple exactly. I12 degrades WARN → **FAIL with inverted sign** *because Arm A retires
nothing*. Addendum G.2's third bind applies directly: a posture that cannot exercise the
mechanism is not a pass, and this one is not even green.

**A genuinely new measurement, which breaks the FFR-3L null for ERCOT:** against **1.534 GW** of
actual ERCOT exits 2023-25, shipped `pipeline` retires **0.000 GW** (recall 0/3) and `legacy`
retires **17.309 GW** (97.1 % false). Both FAIL, violently and in opposite directions. Unlike
FFR-3F the arms genuinely differ, so the I6/I7 flip **is** attributable to the retirement rule at
this window. **The soft latch that reverses the cohort at its own execute_year is the next
blocker** and it is unowned.

### Q.2 — STANDING INSTRUCTION (owner, 2026-08-04): build mechanisms and architecture; do not commission work that a keeper promotion invalidates

Recorded verbatim in substance: *keepers are almost settled, but work must not need repeating
when a new keeper is promoted.*

**What this permits, and why Wave 3/4 complied.** Every lane in Waves 3 and 4 was a mechanism,
architecture, instrument or diagnosis lane. Their deliverables are **code and findings**, which a
keeper promotion does not invalidate. **No Wave-3 or Wave-4 lane has been re-run because a keeper
moved** — and keepers moved constantly through both waves (NYISO eight times in five days; ERCOT,
CAISO, MISO, NEISO and PJM all moved during Wave 4 alone).

**What this forbids.** The work that a promotion *does* invalidate is a **registered forecast or
hindcast RUN**: `scripts/check_forecast_parity.py` resolves each ISO's **CURRENT** keeper →
registry sidecar → bundle `run_config.json` and enumerates its armed mechanisms, so a promotion
re-points the parity target. Its own docstring states the exposure: *"Keeper mechanisms land
weekly, so without a standing check every promotion is another chance to fork the two paths."*
Rule 22 D-5(b) compounds it — a promotion in a `complete` ISO re-keys the marker and
re-verifies its determination.

**Operating rule for the manager, therefore: do NOT commission a full T1-H / T1-X / T1-FF battery
re-measurement until keepers settle.** Charter mechanism, architecture, instrument and diagnosis
lanes freely; they are keeper-agnostic. A run-producing lane is chartered only when its question
cannot be answered any other way — FFR-3Q-3 was one, correctly, because "does the retirement
layer produce events" has no committed-artifact answer.

**One open exposure created by this session and left to the successor:** FFR-3Q-3's arms were
solved before ERCOT's keeper moved to `2026-08-04-ercot165-unpooled-share`. Its **findings are
structural** (the pipeline rule retires nothing; the soft latch reverses at execute_year) and I do
not believe they are keeper-sensitive — but **that is a belief, not a measurement**, and the
successor should either check parity or state the limitation rather than inherit my assumption.
This is the J.1/L.3 discipline applied to my own handoff.

### Q.3 — Wave 4 results, and two charters whose PREMISE was refuted

* **FFR-4A.** The knife-edge is **not** a mis-set `K`. It is a **dimensional double-count** — a
  *stock* (pending pipeline MW) subtracted from two *flow* caps (GW **per year**). Netting a stock
  from an annual-flow cap `C` under lag `L` caps the long-run average decision rate at `C / L`,
  and destroys the ratchet whenever `K ≤ L`. **`K` and `L` both survive with their citations
  intact** — `K = 2.0` independently corroborated against the EIA-860 ratio distribution
  (p90 = 2.20–2.37). The defect is a **third, uncited term**. Recommendation (rule 19): remove the
  pending-stock netting from the flow caps and relocate the anti-cobweb guard to where its
  phenomenon lives. **Unimplemented — needs an owner card.**
* **FFR-4B.** Both landed, MISO-scoped, each measured alone. D-12 wired at **0.3875** (duration-
  weighted mean over MISO's four PRA seasons) and is **not inert — its whole effect is in the
  RETIREMENT screen**, 2024 economic retirements 11,931.6 → 13,524.3 MW, because the reliability
  floor now has real accredited solar. D-2′ armed via `ISOConfig.default_scenario_overrides` with
  the `ScenarioConfig` default left `False`, so no other ISO moves — inert 2022-24, decisive in
  2025: solar flips −33,406 → +25,536 $/MW-yr and decides **1,236.4 MW, MISO's first modelled
  solar entry anywhere in the window**.
* **FFR-4C.** Landed. MISO wind entry **4.0 → 0.0 GW** under the statutory window — the predicted
  direction, larger than predicted. Rule 1 says it stays in.
* **FFR-4D — PREMISE REFUTED.** The shortfall is **47.3 % fleet, 52.7 % accreditation rate and
  class boundary**. Fleet correction recovers +5,540.3 MW and moves the reserve position
  0.8852 → **0.9819, not 1.0896**: CAISO is still **1.8 % short**, the adequacy need does not
  vanish and **row 4's numerator does not collapse**. The charter's own *"if row 4 does not clear
  after the fleet is right, THAT IS THE FINDING"* branch fired, and nothing was tuned in response.
  It also found **FFR-3P's §1.1 hydro row is wrong and reverses sign** (Table 1.1 Hydro includes
  pumped storage): −1,670.2 MW deficit becomes **+292.6 MW surplus**, moving 1,962.8 MW into
  storage (−5,933.2 → −7,896.0 MW). Total unchanged; attribution moved.
* **FFR-4E — PREMISE REFUTED, decisively.** The overlay's absence is a **deliberate,
  already-adjudicated scoping choice**, and the missing ORDC tail **is worth approximately
  nothing**: armed on the lookahead today it adds **$0.0002/MWh**, because MISO's modelled reserve
  never approaches the curve (≥11 GW floor; the curve needs <~8 GW to reach even $2.65/MWh). The
  in-LP mechanism it defers to has non-zero reserve duals in **0/6/2 hours of 8,760**. And on
  MISO's measured 2024 DA prices, everything above $200 contributes **$1,192/MW-yr — 0.9 % of
  CONE**. **FFR-3V's ranking of this as "the largest single suppressor" is refuted.** I chartered
  it on that ranking; the lane cost one diagnosis and returned a decisive null, which is the
  system working.

---

## Addendum R — successor sitting: the Q.2 exposure measured closed, two cards put, Wave 5 opens

**Written 2026-08-05 by the workstream manager (successor session) at `origin/main` `4d8f0c06`.**
Verified at writing, from the artifacts: keepers are Addendum Q's six, unchanged (ERCOT re-read
from its shard, not quoted from a doc). `complete` = {NEISO, NYISO, PJM}; `final` EMPTY; holdout
freeze ACTIVE; zero open PRs. Overnight churn, for the record: PR #3563 (ercot-165 keeper-auditor
repairs) went stale-based and un-mergeable ("dirty", 71 files of carried branch history against
its title's two text repairs) and was closed UNMERGED; a rescue session re-cut the repairs
cleanly and merged them as PR #3565 (`ba2b47d6` → `4d8f0c06`). Nothing remained for this sitting
to do there. Main moved twice during this sitting's own verification pass — the re-verify
discipline is not ceremonial.

### R.1 — Q.2's handed-over exposure, DISCHARGED BY MEASUREMENT: FFR-3Q-3 carries a stated limitation, not an inherited belief

Q.2 (last paragraph) left the successor one exposure: FFR-3Q-3's arms were solved before ERCOT's
keeper moved to `2026-08-04-ercot165-unpooled-share`, and the outgoing manager *believed* the
findings keeper-insensitive without measuring it. Measured now, committed artifacts only, no
solve:

1. **The promotion moved no shipped default.** ercot-165's two new fields land default-neutral —
   `ercot_wtx_curtail_unpooled: bool = False`, `ercot_wtx_panhandle_owner: str = "tie"`
   (`scenarios.py`, diff `68e7bfcd..HEAD`) — and the keeper arms them in the **bundle only**
   (`ercot_wtx_curtail_unpooled=true` / `owner="share"`, per the promotion note in the ERCOT
   shard). ERCOT's `ISOConfig` is untouched in that range (the only `default_scenario_overrides`
   change is FFR-4B's MISO-scoped D-2′ arm). FFR-3Q-3's arms inherited shipped defaults, so
   **the keeper move did not change the config they realized.** The battery's parity re-point to
   the new keeper remains a re-measurement-time concern under Q.2's operating rule — not a defect
   in the FFR-3Q-3 record.
2. **The arms are nonetheless NOT byte-reproducible at today's HEAD — for a reason unrelated to
   the keeper.** D-13 (`7bdc58c6`) added the shipped forecast-path default
   `ira_ptc_credit_window_years: int | None = 10`, which moves wind vintage offers in every ISO's
   forecast/hindcast lane (and moves the cache keys). The other new default-True field,
   `storage_measured_base_fleet`, is gated to backcast mode AND
   `STORAGE_MEASURED_BASE_FLEET_ISOS` (= CAISO; `runner.py:782`), so it cannot touch an ERCOT
   hindcast.
3. **Determination.** FFR-3Q-3's findings stand **as-measured at base `68e7bfcd` under shipped
   defaults** (recorded keys `6a824992b5fb1baf` / `d065923f427349d1`); keeper-insensitivity is
   neither claimed nor needed. No re-run is commissioned for keeper churn (Q.2). **FFR-5A's
   step 0 (R.4) re-verifies the reversal reproduces at its own HEAD** — the one lane that needs
   the phenomenon live is the one that re-measures it. Expected direction of the D-13 delta,
   stated as expectation and NOT as measurement: out-of-window wind vintages' offers rise →
   prices rise → coal screen margins rise → the re-clear, if anything, more likely. If FFR-5A
   finds the reversal does NOT reproduce, the D-13 delta is the first attribution candidate.

### R.2 — CARD D-17, put this sitting: implement the FFR-4A entry-cap fix?

**Measured (FFR-4A, `docs/handoffs/ffr-4a-entry-ladder-2026-08-04.md`; the diagnosis is already
accepted on record, Q.3).** The freeze is a **dimensional double-count**: the pending-pipeline
**stock** is netted from two annual-**flow** caps, capping long-run average decisions at `C / L`
and freezing the ladder ratchet whenever `K ≤ L` — and `(K, L) = (2, 2)` puts **24 of 24**
ISO × entry-tech cells on the knife-edge, at both vintages. `K = 2.0` (ReEDS; corroborated
between the measured p75 and p90 of the EIA-860 growth-ratio distribution) and `L = 2` (LBNL)
both survive with citations intact; the defect is the **third, uncited term**. The documented
intent nets the per-tech cap only; the ladder half of the netting is an implementation extension
(FFR-4A §1.1(b)). The shipped mechanism forbids what the EIA-860 record shows ~30 % of
ISO-tech-years (a new annual-build maximum). Validated end-to-end: FFR-4A's harness reproduces
the registered MISO legs to the MW, and the `C/L` law predicts wind's 4,000/0 alternation and its
2,000 MW mean exactly.

**Recommendation — (a) CHARTER THE IMPLEMENTATION LANE (FFR-5C): land FFR-4A's E-1 + E-2
TOGETHER, as one gated default-OFF field.** Remove the stock netting from **both** flow caps and
make the entry pro-forma **see its own pending pipeline** (`_lookahead_reprice_signal` prices the
current fleet only; pending rows already carry `mw` + `cod_year`, so the relocation is zero-DOF).
One mechanism per phenomenon (rule 19): the throughput caps go back to bounding throughput; the
anti-cobweb guard moves to the information gap that is the actual cobweb. Default OFF with its
matrix row (rule 28c) and a paired arm; the shipped path stays byte-identical until armed.
Pre-registered and carried: **this does not rescue MISO solar's FC-3 band** — that leg's solar
dies on revenue before any cap is consulted (FFR-4A §5.4.3).

**Option (b), delete the netting without relocating the guard — I think this is wrong.** Cost:
the cobweb phenomenon is real (a pro-forma blind to committed-not-online MW re-decides the same
opportunity every lag year); deleting the netting alone un-guards it. Rule 19 wants the guard at
its phenomenon, not removed.

**Option (c), leave as shipped — I think this is wrong.** Cost: every cap the netting touches is
effectively halved (`C/L`); the ratchet is dead in all 24 cells; and E-3's latent trap stands —
the growth factor is `K − L + 1`, so the planned per-tech IA→COD refinement that pushes any
tech's `L` to 3 would **silently zero its economic entry** while every parameter still carries a
valid citation.

**Sign-off D-17:** ☐ (a) charter FFR-5C (E-1+E-2 together, gated default-OFF)
☐ (b) delete netting only  ☐ (c) leave as shipped  ☐ other: ____________  owner: ______  date: ____

### R.3 — D-16 re-put (the Addendum P card, unchanged)

Per the handover queue, D-16 (represent the procurement channel that actually built MISO's
solar — card at the end of Addendum P) is put to the owner this sitting, unchanged:
recommendation **(a) charter a STRUCTURAL SCOPING lane** (design + rule-13 `[R-MEASURED]`
admissibility argument, no implementation — dispatched as FFR-5B if signed); the option I think
is wrong, **(b) disclosed limitation**, carries the cost recorded on the card (MISO's FC-3
additions can never be right for the right reason; every future lane is pushed toward the fitted
revenue adder rule 1 forbids; every capacity-market ISO's VRE build rests on an unmodeled
channel).

### R.4 — FFR-5A chartered: the soft-latch root cause (the FH-4/FH-5 blocker) — Wave 5 opens

Manager charter, no owner card — the same manager-charterable class as FFR-4E (P.3(b)): it
diagnoses why an **existing** mechanism behaves as measured and proposes nothing. The question
(Q.1; FFR-3Q-3 §3.5, §7.1): why does the soft latch (`retirements.py` pipeline component 3)
re-clear a 29-unit / 8,218 MW coal cohort at 2024 — its own `execute_year` — on 2023 dispatch
($15.77/MWh system mean) that is *cheaper* than the 2021 dispatch that failed them ($23.40)?
First suspect on record: the reserve leg of the attainable margin
(`screen_reserve_value_enabled` on). Until a decided cohort survives to execution, the exit half
of the retirement layer cannot be exercised and FH-4/FH-5 cannot lift (Q.1) — this lane owns the
blocker. **Q.2 compliance:** the deliverables are findings plus a ledger instrument (a
margin-component enrichment of `pipeline_events` rows — not a tunable); the diagnostic solve is
chartered under Q.2's own exception because the per-unit screen-margin decomposition exists in
**no committed artifact** (T1-FF bundles are slim by convention, zero parquets, and `results/`
dies with the container). Prompt: pack §0k. Model: FABLE (rule 27 — `src/` instrumentation in
scope; and this is the program's hardest open root cause).

### R.5 — signatures this sitting

Both cards signed 2026-08-05, each on the stated recommendation, via the option cards put in this
sitting:

| decision | signed | what it authorizes |
|---|---|---|
| **D-16** | **(a) CHARTER STRUCTURAL SCOPING LANE** | **FFR-5B**: design + rule-13 `[R-MEASURED]` admissibility argument for the procurement channel — what drives volume, how it regenerates in a forward year, what data identifies it. NO implementation, no solve, no parameter proposed as a number. Implementation is a separate, later owner decision, and the lane delivers a proposed card for it |
| **D-17** | **(a) CHARTER FFR-5C** | Land FFR-4A's E-1 + E-2 **together**: the stock netting removed from both flow caps AND the pro-forma made pipeline-aware, as ONE gated default-OFF `ScenarioConfig` field with its matrix row (rule 28c) and a paired-arm measurement. The shipped path stays byte-identical until armed; arming anywhere is a separate decision |

Consequences recorded once (the O.2 pattern), so no lane re-opens them:

* **D-16(a) may return a null.** A finding that no rule-13-admissible design exists is a valid
  deliverable; the lane says so plainly rather than forcing a design into existence.
* **D-17(a) is a correctness change gated OFF.** Nothing moves in any keeper, forecast default,
  or registered run until a separate arming decision. Anyone reading FFR-5C's PR as "fixes MISO
  solar" has it wrong (FFR-4A §4/§5.4, pre-registered and owner-accepted at Q.3): that leg's
  solar dies on revenue before any cap is consulted.

**Wave 5 is therefore three lanes: FFR-5A [FABLE] (R.4, manager-chartered), FFR-5B [OPUS]
(D-16a), FFR-5C [OPUS] (D-17a).** All three run as independent sessions (rule 12 is per prompt,
Addendum F.2; sessions do not contend). `src/` overlap: none (5A: `retirements.py`; 5C:
`new_entry.py`/`runner.py`; 5B: docs only). The one shared surface is the mechanism matrix —
whichever session lands second re-checks its cell survived the merge (the O.3 discipline).
Prompts: pack §0k.

---

## Addendum S — refresh sitting: Wave 5 landed same-day; the price-object card, the procurement card, and the CAISO grant

**Written 2026-08-05 (~04:30Z) by the workstream manager at `origin/main` `c750e3f9`.** Between
R.5 (~01:10Z) and this refresh, ELEVEN PRs merged (#3567–#3576, #3578) and Wave 5's three lanes
all ran: FFR-5A and FFR-5B are LANDED, FFR-5C is IN FLIGHT (PR #3577 open, its 3/3 stack:
`entry_pipeline_aware_signal` + matrix row + handoff). Verified off the artifacts at this HEAD:

* **Keepers: two moved.** CAISO → `2026-08-05-caiso-174-measured-fleet` (the FFR-4D epoch
  re-solve; `storage_measured_base_fleet` measured a NULL there), NEISO →
  `2026-08-05-neiso-83-ca1-reclass`. ERCOT/PJM/NYISO/MISO unchanged from Q's list.
* **NEISO's D-5(b) re-key: VERIFIED EXECUTED** by the promoting session — the `complete` entry's
  `keeper` field reads `2026-08-05-neiso-83-ca1-reclass` and `keeper_at_declaration` is
  preserved (`2026-07-08-neiso-54-steamgas-ct`). Read off the marker file, not inferred. CAISO
  holds no marker; nothing to re-key on its promotion.
* `complete` = {NEISO, NYISO, PJM}; `final` EMPTY; freeze ACTIVE. calibration-program lanes also
  landed (nyiso-127 seam exoneration + default-off PAR attribution; miso-130 C7 diagnosis;
  ercot-166/167 probes + `ercot_storage_as_soc_reserve`; rubric v3.0 ledgered-caveat kind) —
  noted for state, none in FFR/FH scope.

### S.1 — Wave 5 lane adjudications

**FFR-5A (PR #3575) — the soft latch is root-caused, and the answer changes the question.**
The reversal reproduces at HEAD on the recorded key. The reserve leg — FFR-3Q-3's first suspect,
carried in R.4 — is **adjudicated DEAD: $0.0/kW-yr at both screens** (do not re-suspect it).
The mover is the **bar's PRICE OBJECT**: the decide screen consumed raw 2021 duals + overlay
(the rule-22 bridge guard suppresses the lookahead when the entering year is the bridge,
`runner.py:2545-2546`) and failed the cohort at $22.4 vs the $58.5 bar; the reverse screen
consumed the lookahead stack-reprice (mean $65.38/MWh vs raw $15.77 — 4.1×; 122 manufactured
pro-forma scarcity hours on a 34.8 %-RM fleet) and cleared all 29 units at $341.5 — six times
the bar, 100 % energy leg. **On a consistent basis there is no counter-price paradox and no
reversal** ($1.3/kW-yr on raw 2023 duals, 0/29 clear — the cohort would have executed 8.2 GW).
The latch's logic matches its design record exactly; **its INPUT is the defect** (the design
presumes one bar; the screen sequence delivers two). Hysteresis is measured MOOT (no band
< $283/kW-yr survives a 6×-bar clearance). And the class-(c) rider: **neither consistent basis
reproduces the real 1.534 GW** — raw duals fail the entire 66.9 GW merchant fleet, the lookahead
clears everything — so the pipeline's output is currently determined by bridge geometry, not
unit economics. Escalated as the owner's price-object decision → **CARD D-19 (S.3)**. Cell
`economic_retirement_screen` ERCOT `fc` correctly stays O. Run registered
`ercot-2021-2025-t1ff-armr-ffr5a-pipeline`.

Two successor-facing notes from the lane, recorded here so they are not lost: (i) **the D-13
hash-out cache hazard** — `ira_ptc_credit_window_years` lands at a hash-dropped default, so the
SAME cache key spans behaviorally-different configs across the D-13 boundary; cold solves and
D-10 make it harmless today, but never read byte-identity into "same key" across that boundary.
(ii) FFR-3Q-3's ledger reserve margins drifted at the identical key (40.9/49.0 → 39.8/47.8 for
2024/2025) — that is D-13 moving later-year fleets, the same hazard seen from the other side.

**FFR-5B (PR #3574) — the D-16 design returned a PARTITION, and the partition is the finding.**
(i) The near-term committed-procurement gap is real and rule-13 ADMISSIBLE: a default-OFF VRE
limb of step 4's known-additions channel, keyed to the run's own EIA-860 proposed-generator
vintage at construction-committed status (U/V/TS) — the additions-side twin of the
confirmed-retirement registry, zero free parameters, measured coverage median 0.63/0.33/0.21 of
realized solar COD at horizons 1/2/3 yr. Proposed as **CARD D-18, adopted verbatim (S.2)**.
(ii) The long-run policy-procurement half is **REFUSED a channel** (rule 19): the phenomenon
already belongs to the RPS LP row, whose defect is its SPATIAL GRAIN (one ISO-wide row against a
load-weighted state blend dilutes a binding MN 55 %-by-2035 to slackness) — escalated as
**FFR-5B E-1/E-2**, "the largest single finding in this lane," queued for its own scoping
decision next wave, deliberately not put today. (iii) Corporate PPAs / beyond-horizon
procurement have **no admissible representation**: disclosed as a named null; sizing it is a
cheap committed-artifact follow-up, unchartered. Pre-registered so no one misreads: the
admissible channel **cannot and must not** close MISO's 18.649 GW (a vintage-2020 hindcast may
see 1.034 GW of committed pipeline; reproducing five-year build from a two-year queue would mean
the information gate failed).

**FFR-5C — in flight.** PR #3577 open. Landed second of the 5B/5C pair, so the O.3 interaction
re-check is its duty. No action from this sitting; the two lanes chartered below both branch
AFTER it merges (same code surfaces).

**Numbering note:** FFR-5B minted "CARD D-18" in its committed handoff; adopted as-is
(correct-by-addendum: a committed record is not renumbered). The FFR-5A price-object card is
therefore **D-19**.

### S.2 — CARD D-18 put: implement the near-term VRE procurement channel?

The card as drafted in `ffr-5b-procurement-channel-design-2026-08-05.md` §7 is put to the owner
verbatim, with its recommendation and both wrong options carried: **(a) RECOMMENDED — charter
the implementation lane** for the near-term channel ONLY (`vre_procurement_additions_enabled:
bool = False`, MISO-scoped arming decision separate, matrix row in the same PR, paired arm;
carried: does not close MISO's gap, and the FFR-3V §6.1 renewable-pool vintage leak is a
BLOCKING PRECONDITION for the hindcast arm only — plain 2026+ forecasts unaffected).
**(b) widen the status basis** — the option the evidence will keep suggesting; cost: admits
announcement-grade `P` rows, the tier this repo excluded by name on both sides; a fitted input
arriving as a status filter. **(c) disclosed limitation** — cost: the merchant screen stays a
single point of failure for ALL VRE in EVERY forecast while the accurate, already-intaken
pipeline sits unread on disk next to the thermal channel that reads it (rule 14).

### S.3 — CARD D-19 put: which price object do the capacity screens own?

**Measured (FFR-5A §§2-6).** The option space is FFR-5A §6.1's, enumerated there without
recommendation; the manager's recommendation follows from the lane's own measurements:

**Recommendation — (a) CHARTER ONE LANE (FFR-5D): unify on the LOOKAHEAD object everywhere in
the capacity screens (§6.1 option 2) AND repair its measured completeness gaps (§6.1 option 4),
together, gated default-OFF.** Structure: the real market's exit/entry decisions are forward
pro-formas, so the lookahead is the structurally faithful KIND (rule 1) — and it is the FF-2A
answer to the s2/s3 revenue understatement, so reverting to raw duals re-opens a solved defect.
But its LEVEL is broken by three identified completeness gaps (thermal-only stack omits storage
entirely; net load subtracts prior-year VRE OUTPUT rather than entering-year capacity;
time-mean availability applied to peak hours) that jointly manufacture 122 scarcity hours on a
34.8 %-RM fleet. Unify (one object at every screen, bridge-adjacent included — rule 19, and
rule-22-safe since the full-forward leg's growth-scaled fallback reads nothing measured) and
repair (each gap from existing model state; **any repair requiring a new tunable escalates
rather than lands**). Paired arms on the FFR-5A posture; leave-one-year-out within 2023-2025
before any promotion; per-ISO verdicts (rule 25) even though the function is ISO-agnostic code.
Dispatches AFTER PR #3577 merges (same function).

**The options I think are wrong, with their measured costs:** **(§6.1 option 3) raw duals
everywhere** — measured: the ENTIRE 66.9 GW merchant fleet fails the bar (582-unit
entry_capped churn; the cohort executes 8.2 GW and the cap admits successors, against 1.534 GW
of actual exits), and s2/s3 re-opens. **(§6.1 option 1) pin each cohort to its decide-screen
object-kind** — cheapest, and fixes the reversal artifact; cost: bridge geometry still selects
which bar each cohort lives under (two live cohorts screened on different objects), and the
signal gains no power to resolve real exits — the class-(c) rider stands in full. **(§6.1
option 2 alone, no repair)** — bakes in "nothing ever retires" at the measured level
($267-341/kW-yr vs $21-58 bars, every fuel clearing 4-13×).

### S.4 — CARD put: grant CAISO `complete`?

The recommendation now exists twice on record: caiso-171 (assessment reversed to YES at
`0043fc22`, P.6 — criterion restated by the owner: `complete` means (a) the 2022 touchpoint is
allowed and (b) frontier, everything testable tested; NOT a DOF-cleanliness certificate), whose
one gating item (the PGE-TAC weight) was closed MEASURED by caiso-172; and caiso-174 (PR #3578),
which re-solved the FFR-4D epoch, put the keeper on the measured fleet, and **re-recommends
`complete` = YES post-epoch**. **Recommendation — (a) GRANT.** The freeze stays active and
orthogonal (NYISO and PJM were declared complete six days INTO it; the grant authorizes the
2022 ladder, the freeze suspends spending it), and the grant anchors D-5(b) re-keying for every
future CAISO promotion. Execution if signed: a small governance lane writes the marker entry
keyed to `2026-08-05-caiso-174-measured-fleet` with its determination verified via
`scripts/calibration_verdict.py --run-id` (committed artifacts only, never a solve) and runs
`scripts/audit_keepers.py` M1. **The option I think is wrong: (b) defer until the freeze
lifts** — cost: it re-conflates the marker with the freeze (the exact confusion caiso-171's
first NO rested on and then corrected), and it protects nothing the freeze does not already
suspend.

### S.5 — signatures this refresh

All three signed 2026-08-05, each on the stated recommendation, via the option cards put in this
refresh:

| decision | signed | what it authorizes |
|---|---|---|
| **D-18** | **(a) CHARTER THE CHANNEL LANE** | **FFR-5E**: the default-OFF VRE limb of step 4 (`vre_procurement_additions_enabled: bool = False`), U/V/TS statuses at face value, matrix row in the same PR, paired-arm measured. Arming anywhere (including MISO) is a separate decision (rule 25). FFR-3V §6.1 remains the BLOCKING PRECONDITION for the hindcast arm only |
| **D-19** | **(a) UNIFY ON LOOKAHEAD + REPAIR** | **FFR-5D**: one price object at every capacity screen (bridge-adjacent included, via the growth-scaled fallback — rule-22-safe) plus the three completeness repairs (storage in the stack, entering-year VRE capacity, peak-hour availability), as ONE gated default-OFF field, paired arms on the FFR-5A posture, LOYO 2023-2025 before any promotion; a repair that needs a new tunable escalates rather than lands |
| **CAISO `complete`** | **GRANT** | A governance lane writes the CAISO `complete` entry keyed to `2026-08-05-caiso-174-measured-fleet`, determination verified via `scripts/calibration_verdict.py --run-id` (committed artifacts only, never a solve), `audit_keepers` M1 after. Spending 2022 stays suspended by the active freeze; `final` untouched |

Consequences recorded once (the O.2 pattern):

* **FFR-5D and FFR-5E both BRANCH AFTER PR #3577 MERGES** (still open at this writing —
  re-checked after S was pushed; the interim main move was #3579, an ercot-167 control run).
  FFR-5C owns the same code surfaces (`_lookahead_reprice_signal`; the entry budget netting);
  each lane's step 0 verifies the merge and re-reads the landed code.
* **D-19(a) does not promise the exit gates go green.** The repaired object's level is a
  measurement to be made, not a target to be hit. If the unified, repaired signal still cannot
  resolve the real 1.534 GW, that is the finding (rule 1) and FH-4/FH-5 stay blocked on it.
* **The CAISO grant authorizes the validation ladder and NOTHING else.** `final` is untouched;
  the freeze suspends spending until it lifts; the grant's execution follows the NYISO/PJM entry
  shape and cites this addendum as the session-logged owner authorization.

**Wave 5 is now six lanes: 5A ✅ · 5B ✅ · 5C in flight (#3577) · 5D [FABLE] · 5E [OPUS] ·
CAISO-GRANT [OPUS].** Prompts: pack §0l. Open queue carried forward: FFR-5B E-1/E-2 (RPS
spatial grain + clean tiers — next wave's scoping card), the §5.4 residual sizing, FFR-3V §6.1
(now blocking FFR-5E's hindcast arm), FFR-4D's 52.7 % accreditation half, the CAISO anchor
(D-15 posture), and the pre-existing test failures on main.

## Addendum T — Wave-5 lanes adjudicated: CAISO-GRANT and FFR-5E CLEAN, FFR-5D partial (measurement outstanding)

**Written 2026-08-05 by the workstream manager at `origin/main` `34473b0c`.** Context: the §0l
prompts were never pasted (owner confirmation, recorded in pack §0n); after the manager
re-dispatched them at `70acd78c` all three lanes ran the same morning. Everything below is
verified off committed artifacts at this HEAD, not inherited from lane self-reports.

### T.1 CAISO-GRANT — LANDED, ADJUDICATED CLEAN (PR #3599)

`complete` now reads {CAISO, NEISO, NYISO, PJM}. The determination was scorer-verified against
the named run (`CALIBRATED-WITH-CAVEATS`, 0 FAILs, the two caveats being the owner's
2026-07-30 act at caiso-145, no new slot spent), `audit_keepers --iso CAISO` M1 PASS,
mechanism-matrix zero-delta, `locked_test` note "never authorized", and the lane PROVED live
that the freeze outranks the marker (`--year 2022 --holdout-authorized` refused citing the
freeze first). D-5(b) now applies to every future CAISO promotion. Two disclosures adopted
into the record:
* **caiso-174's committed bundle carries no `legitimacy_diagnostics.json`**, so C7/C8 are
  unscored-protective on the current keeper (the superseded caiso-172 scored both PASS).
  Disclosed-not-disqualifying per the NEISO precedent; the close-out is scorer-only (rule 21:
  no re-solve) and CHEAP — queued as a manager-charterable follow-up.
* **The `ruff-autofix.sh` PostToolUse hook reflows `src/market_sim/config/constants.py`
  (3,960 → 9,508 lines) on ANY `.py` Write/Edit** — pre-existing on main (`ruff format
  --check` fails against main's own bytes; the file is not in `extend-exclude`). The grant
  session caught it and restored exact HEAD bytes unstaged. This is a rule-27 footgun for
  every session that touches any Python file: NEW STANDING TRAP (check `git status --short`
  for constants.py before staging; never push the reflow). The underlying lint-config fix is
  unowned — small, but it edits `pyproject.toml`/hook behavior, so it gets its own charter.

### T.2 FFR-5E — LANDED, ADJUDICATED CLEAN (PR #3602 chain, D-18(a) discharged as chartered)

`vre_procurement_additions_enabled: bool = False` (verified at HEAD), forecast-mode-only,
matrix row in the same PR (28c), zero free parameters. Byte-identity proven the strong way —
shipped digest identical between the base commit (field absent) and the feature commit, pinned
default `cache_key()` unmoved. Measurement by the FFR-4A harness pattern (evolve step-4/5
direct, six ISOs × 2026-2029, no LP, no run produced ⇒ rule 15 N/A): the MISO-2027
demonstration shows one physical queue spent once (armed = 2,489.3 economic + 2,510.7 procured
= 5,000.0 MW, exactly the budget an un-netted channel would have overshot), and MISO-2028
shows the closed defect (shipped builds nothing, armed commissions 960 MW committed pipeline).
The hindcast arm was BLOCKED per FFR-3V §6.1 and the lane honored the block. Rule 13's
boundary is enforced mechanically (a loader spy fails on any `operable`/`retired` read). The
lane's guard sentence — this does not and cannot close MISO's 18.649 GW — precedes every
number, as chartered. Two self-caught defects (gate enforced only at one call site; the
cache-key registration miss that would have invalidated every cached bundle) were fixed and
regression-pinned before merge. **New unowned finding, recorded:** `assign_zone_by_coords` has
incomplete zone rules for PJM and MISO (every PJM row falls back to `PJM_AEP_Ohio`) — a
pre-existing condition shared identically with the thermal limb, measured not introduced.
**Arming anywhere, including MISO, remains a SEPARATE owner decision (rule 25)** — no card put
until there is measurement worth deciding on.

### T.3 FFR-5D — PARTIAL: implementation LANDED, paired-arm measurement NEVER RAN

PR #3601 chain landed `capacity_screen_unified_lookahead` (default OFF, cache-key-registered,
byte-identity proven by test), the unification (one signal per entering year, bridge-adjacent
included, rule-22 compliance by construction with quarantine assertions untouched), all three
level repairs (storage peak-shave into the stack; entering-year VRE capacity; hourly
availability — none escalated, zero new tunables), the matrix row, the §2 PRE-REGISTERED reads
(committed before any solve — the discipline held), and the read-out probe
`scripts/probes/ffr5d_paired_arm.py`. **But handoff §3 ("Measured results") and §4
("Governance position") are empty placeholders, there are no
`ercot-2021-2025-t1ff-armr-ffr5d-{shipped,unified}` entries in `frontend/data/hindcast/`, and
no PR comment explains** — the two pre-registered invocations (4 cold LP years each) evidently
never completed in that container. Not a lane failure: the pre-registration makes the
continuation purely mechanical. **FFR-5D-M chartered** (prompt: pack §0o) — run the two §2
invocations exactly, execute the probe, register both arms, fill §3/§4 by appending. It
qualifies under Q.2 (no committed-artifact answer exists).

### T.4 Standing consequences

* **Wave-5 close: NOT RUN** — blocked solely on FFR-5D-M's measurement.
* **FH-4/FH-5: REMAIN BLOCKED** (I.1). The S.5 rider is unsatisfied by construction — the
  D-19(a) measurement does not exist yet. The lift determination stays with the manager and
  will be adjudicated against G.2's three binds when FFR-5D-M lands.
* **Keeper churn during the window, R.1-checked at each step:** ERCOT moved twice (run167b
  → `2026-08-05-run168b-year-curves`, ercot-168 promotion). Verified at `34473b0c`:
  `ercot_storage_as_*` all default False, `coal_perplant_offer_yearly` default False — the
  shipped posture FFR-5D-M's arms inherit is unchanged. Q.2 stands: no T1 battery
  re-measurement.
* **Owner governance act, recorded (not an FFR/FH lane):** the holdout freeze was
  lifted-spent-re-armed in one owner-signed session (PJM 2022 + NEISO 2022 validation
  touchpoints, PRs #3603/#3606; AskUserQuestion disposition "Lift, spend, re-arm" recorded in
  `holdout-freeze.json` history). Validation tier only, `final` untouched, freeze back ACTIVE
  on its original 2026-07-25 basis. The manager verified the history entries carry the owner
  authorization verbatim.
* **Open queue delta:** ADD caiso-174 `legitimacy_diagnostics.json` close-out (scorer-only,
  cheap); ADD the ruff-autofix/constants.py lint-config fix (unowned); ADD
  `assign_zone_by_coords` PJM/MISO zone rules (unowned, shared with thermal limb). CARRIED:
  E-1/E-2 scoping card (next sitting), FFR-5B §5.4 residual sizing, FFR-3V §6.1 (still blocks
  FFR-5E's hindcast arm AND now gates the useful half of any future arming card), FFR-4D
  row-4, CAISO anchor (D-15), pre-existing test failures.

## Addendum U — FFR-5D-M adjudicated; the FH-4/FH-5 lift determination (HELD); Wave 5 CLOSED

**Written 2026-08-05 by the workstream manager at `origin/main` `8693b75d`.**

### U.1 FFR-5D-M — ADJUDICATED CLEAN (PR #3611)

Verdict-grade continuation: both §2 invocations run VERBATIM as two concurrent cold jobs;
comparability re-verified at its own head; the shipped arm reproduces FFR-5A's §2(a)/§2(c)
records EXACTLY on the identical runtime key `6a824992b5fb1baf`, so the paired delta is the
mechanism's, not drift's. Manager-verified independently at this HEAD: both hindcast sidecars
registered (`ercot-2021-2025-t1ff-armr-ffr5d-{shipped,unified}`, never the backcast registry);
pre-registration integrity holds (git diff from the pre-solve commit shows ZERO altered lines
above the §3 marker); the matrix cell keeps verdict `O` with the full measured citation and
correctly reserves adjudication to the manager; `leakage_violations: []` in both metas (2022
bridged, never read). Nothing armed, promoted, or tuned. The §2 honest expectation held in its
sharpest form and the number came to the manager as-is — the discipline throughout this chain
(FFR-5A → 5D → 5D-M) is what makes the determination below possible.

### U.2 THE FH-4/FH-5 LIFT DETERMINATION — **HELD, NOT LIFTED** (I.1; fifth hold, first on the unified object's own measurement)

Adjudicated against Addendum G.2's three binds and S.5's rider, off the registered arms:

* **Bind 1 (a control that flips identically is not the fix's green): PASSES.** The control
  did not flip — byte-reproduction of FFR-5A on the same key. Attribution is clean.
* **Bind 2 (inverted-sign invariants): FAILS.** The retirement layer swings −100 % → +613.5 %:
  a single 45-unit / 10.9 GW ALL-gas_st exit wave (actual gas_st exits: 0.0 GW), decided at
  the Uri-priced 2021 screen and executed in the pre-window 2022 bridge-ledger year. Unit
  recall 0/3 in BOTH arms; coal — the fuel that actually exited — first decides at the 2024
  screen with execution 2027, also outside the window.
* **Bind 3 (vacancy is not validation): FAILS.** Inside the scored 2023–2025 window both arms
  execute nothing. The in-window exit path remains untested at both postures.
* **S.5's rider is unsatisfied on its own terms.** A cohort now decides AND executes under the
  unified object — the necessary evidence exists — but the object is not yet *defensible* for
  exit validation: at the repaired level the margin bar fails essentially the whole merchant
  fleet (entry_capped 554–564 units / 63.0–66.1 GW in 2024/2025) and the adequacy admission
  cap does ALL the retention work. FFR-5A §6.3's both-bases-fail finding SURVIVES the level
  repairs: the pipeline's output is still governed by cap geometry, not unit economics.
  Validating FH-4/FH-5 against that layer would measure the cap.

**What would lift:** (i) a measured decomposition showing the repaired-level margin failure is
a completeness defect with an identified, rule-13-admissible fix (→ card D-20 below), and
(ii) a non-vacuous in-window exercise of the exit path under whatever that fix produces. FFR-5D
reporting green was never the bar; this is what the bar looks like now that it is measurable.

### U.3 WAVE 5 — CLOSED

All six lanes landed and adjudicated: **5A** (soft-latch root cause; reserve-leg suspect dead)
· **5B** (procurement partition design; D-16 discharged, D-18 signed, E-1/E-2 escalated) ·
**5C** (entry_pipeline_aware_signal; FFR-4A chain closed) · **5D + 5D-M** (unification + level
repairs landed; paired-arm measurement executed; U.1/U.2) · **5E** (VRE procurement channel;
D-18(a) discharged) · **CAISO-GRANT** (CAISO `complete`; D-5(b) now binding on CAISO
promotions). Wave-close checks: every new `ScenarioConfig` field default-OFF with a matrix row
in its landing PR (28c) and every tested cell stamped with citations, rejections included
(28b); registrations confined to their correct namespaces; no lane touched a keeper, marker,
or the freeze; byte-identity proven in every implementation lane; both mid-wave keeper-churn
events R.1-checked (no shipped default moved). The wave's residue is fully enumerated: card
D-20, cards E-1/E-2, FFR-5B §5.4 residual sizing (manager-charterable), FFR-3V §6.1 (blocks
FFR-5E's hindcast arm and any arming card's hindcast evidence), and Addendum T's three adopted
follow-ups (caiso-174 legitimacy sidecar, ruff-autofix/constants.py, assign_zone_by_coords).

### U.4 Cards put at this sitting

* **D-20 — the repaired-level margin gap.** With the honest price object, the retirement
  screen fails ~66 GW of merchant fleet and cannot reproduce 1.534 GW of real exits; either
  the screen object is missing a real revenue leg or the bar is mis-leveled. Manager
  recommends a measurement lane (margin-gap decomposition against the Potomac-SOM net-revenue
  benchmark — the screen's own cited definition), committed-artifact-first, no tuning.
* **E-1/E-2 — the RPS row's spatial grain + the clean/carbon-free tiers** (FFR-5B §5.3,
  "the largest single finding in this lane"). Settled together, never separately. Manager
  recommends a design-only scoping lane on the FFR-5B pattern before any implementation.

Owner dispositions to be recorded by addendum when signed.

### U.5 Owner signatures (same sitting, 2026-08-05)

Both U.4 cards signed AS RECOMMENDED via AskUserQuestion:
* **D-20(a) — SIGNED:** charter **FFR-6A**, the repaired-level margin-gap decomposition
  against the Potomac-SOM net-revenue benchmark. Measurement lane, committed-artifact-first,
  no tuning. Its output is the candidate evidence for U.2's lift condition (i); the lift
  itself stays the manager's.
* **E-1/E-2(a) — SIGNED:** charter **FFR-6B**, the design-only scoping lane settling the
  zonal RPS row grain and the clean/carbon-free-tier question TOGETHER, on the FFR-5B
  pattern. The FFR-5B §5.4 residual sizing (manager-charterable, committed-artifact) rides
  along as a bounded second deliverable.
Prompts: pack §0p. These two lanes open Wave 6.

## Addendum V — Wave 6 measured out: the gap is the price object; the RPS row's real defects; cards D-21/D-22

**Written 2026-08-06 by the workstream manager at `origin/main` `e2ea0b59`.** Both Wave-6
lanes landed within hours of dispatch and are adjudicated below off their committed
artifacts.

### V.1 FFR-6A — ADJUDICATED CLEAN (PR #3628)

Reproduction rigor: the unified arm re-run reproduced FFR-5D-M on the identical runtime key
`49eac64f146b3460` with a byte-identical `crossover_score.json`; reads pre-registered before
ledgers were read; SOM intake bounded to 2023–2025; nothing tuned, armed, or re-registered.
The three chartered answers, measured:
* **(a) The gap is not a missing product leg — it is the missing scarcity content of the
  energy price itself.** At the repaired forward screens every fossil class earns 0.04–4.4 %
  of its measured-price margin (e.g. gas_cc $3.79 vs replica $86.7 vs SOM $89, 2024); the
  object generates ZERO hours > $100 where the measured tail carries 37–88 % of attainable
  margin. The FFR-5A reserve-leg $0.0 was RE-MEASURED at the repaired level as chartered:
  still $0.0 — and now shown CONSISTENT with the 2024/25 market's own ≈-zero AS-product
  share. The 2023 reserve gap enters through the ENERGY price (ECRS effects), not the leg.
* **(b) The bars are exonerated** — externally consistent within ~5 %, wrong sign to explain
  anything. Standing refusals recorded: verdict rows 3 (bar re-leveling at a residual) and
  4 (any signal-scaling knob) are REFUSED BY NAME; future lanes cite, never re-argue.
* **(c) THE BOUNDING FINDING: ERCOT's true margin-driven exit total 2021–2025 is ≈ 0 GW.**
  The 1.534 GW scoring target decomposes into a paper event outside the fleet basis (Deely,
  physically dead 2018, status OS), a margin-positive municipal fleet-plan exit (Decker,
  3.7× its bar at exit), sub-grain small units — and it MISSES the window's one real
  > 300 MW gas_st exit (Braunig, status OS not RE, dropped by `build_capacity_actuals`).
  A correct margin screen SHOULD retire ≈ nothing in this window. 1.534 GW is not a
  margin-screen target and no admissible fix may chase it.

### V.2 FFR-6B — ADJUDICATED CLEAN (PR #3626), with ONE manager correction

The correction: the lane's proposed card titled itself "CARD D-19" — that number is SPENT
(D-19(a), lookahead unification, Addendum S.3). **Renumbered D-22 by the manager**; recorded
once here, cited hereafter (the J.1/L.3/P.1 pattern: correct by addendum, no re-litigation).
Substance, measured: **E-1's diagnosis needed correcting** — the defect is not ISO-wide-ness
but a silent free-intra-ISO-REC-trade assumption, TRUE in four ISOs (their single rows are
arithmetically EXACT) and FALSE only in MISO (MCL 460.1029: Iowa's surplus is paying
Michigan's bill; MISO-East 24.7 pp deficit at zone grain vs 0.2 pp ISO-wide). **E-2 binds
only at that same grain** (MISO-West 14.0→29.4 pp, MISO-East 21.7→33.1 pp; ISO-wide it is
slack every year; Illinois is a recorded null — CEJA is not an LSE share obligation).
**And a §8 cross-cutting defect that outranks both:** NYISO/NEISO/CAISO encode clean-tier
statutory targets on the renewable-only row with under-counted eligible sets (NYISO 20.2 pp,
CAISO 7.1 pp), pinning those rows' duals at the ACP ceiling — a permanent, mechanism-
generated $40–50/MWh entry subsidy in three ISOs with no statute behind it. The rider
delivered the §5.4 residual: 35–73 % of realized 2021–25 VRE build has no admissible
representation at h=1 (85–96 % at h=2) — an upper bound and a disclosure number, never a
target. PJM/NEISO zonal rows REFUSED ON STRUCTURE (their compliance regions ARE the ISO;
PJM zones cut Pennsylvania three ways). E-1 must never acquire a build limb.

### V.3 The FH-4/FH-5 lift, restated on measured grounds — STILL HELD

U.2's condition (i) is DELIVERED: FFR-6A identifies the repaired-level failure as a
completeness defect with a rule-13-admissible fix (scarcity restoration from published
market design — ORDC parameters, RDPA, AS demand curves, uncertainty at the stack grain —
plus the inherited fleet-length knot, additions 17.0 vs 55.4 GW actual). Condition (ii) is
RESTATED per V.1(c): a "non-vacuous in-window exercise" was the wrong test — the true
in-window answer IS ≈ 0 economic exits. Validation of the exit half now means, measured on
a defensible object: (α) the screen retires ≈ nothing in-window for economic cause, (β) the
false pre-window 10.9 GW gas_st wave is GONE, and (γ) the fixed actuals target (D-21(b))
shows instrument-driven exits carried by their own channels. FH-4/FH-5 remain BLOCKED until
a lane demonstrates (α)–(γ); the determination stays the manager's (I.1).

### V.4 Housekeeping verified

caiso-175 promoted with the FIRST exercise of CAISO's D-5(b) re-key duty — executed
correctly (`keeper` → caiso-175, `keeper_at_declaration` preserved, determination
RE-VERIFIED on promotion without a solve) — and the lane itself closed Addendum T's
caiso-174 C7/C8 follow-up (legitimacy sidecar now scored). STRUCK from the open queue.
Only ScenarioConfig field added since U: `nyiso_solar_market_generator_basis` (default
False). Shipped posture intact.

### V.5 Cards put at this sitting

* **D-21 (FFR-6A follow-ons):** (a) charter the forward-object scarcity-restoration
  diagnosis [the FH-4/FH-5 critical path]; (b) charter the scoring-target hygiene fix
  (verdict rows 5a/5b) with 5c (honor announced fossil dates in hindcast) put as an
  explicit refuse-or-adopt; (c) ECRS measured AS quantities — manager disposition DEFER
  until a lane must reproduce 2023-level revenues (no card needed now).
* **D-22 (renumbered from FFR-6B's proposed "D-19"):** the RPS/clean-tier lane — options
  (a) one lane three arms in order / (b) E-1 first / (c) zonal everywhere / (d) nothing;
  manager concurs with the lane: (a).
Dispositions to be recorded by addendum when signed.

### V.6 Owner signatures (same sitting, 2026-08-06)

* **D-21(a) — DEFERRED (owner decision, against the manager's recommendation).** Recorded
  once with its measured consequence, per the standing protocol: the scarcity-restoration
  diagnosis is the only lane that can produce lift conditions α/β (V.3), so **FH-4/FH-5
  remain blocked with NO open path to the lift** until the owner re-opens D-21(a); the
  capacity-evolution chain continues to run on a forward object measured at 0.04–4.4 % of
  real margins, retained by the admission cap. Q.2 (no T1 battery re-measurement) stands.
  No session re-litigates this; a future sitting may re-open it.
* **D-21(b) — SIGNED AS RECOMMENDED: hygiene only, 5c REFUSED.** Charter **FFR-7A**: the
  scoring-target fixes (verdict rows 5a/5b — OS-status vintage handling, `build_capacity_
  actuals` beyond status-RE). 5c (announced fossil dates in hindcast) is REFUSED and
  recorded as such — cite, don't re-propose.
* **D-21(c) — manager disposition stands:** ECRS quantities deferred until a lane must
  reproduce 2023-level revenues.
* **D-22(a) — SIGNED AS RECOMMENDED:** charter **FFR-7B**, one lane, three arms, in order
  (Arm 1 tier/eligible-set level fix NYISO/NEISO/CAISO → Arm 2 K-row generalization, MISO
  armed only → Arm 3 clean-tier rows, MISO-West/East). §45U-vs-clean-dual composition stays
  OPEN and blocks Arm 3's arming only. E-1 never acquires a build limb.
Prompts: pack §0r. Wave 7 opens with FFR-7A and FFR-7B.

## Addendum W — FFR-7A adjudicated (with a real surprise); rule-22 regime change; FFR-7B in flight; FFR-7C chartered

**Written 2026-08-06 by the workstream manager at `origin/main` `82765525`.**

### W.1 FFR-7A — ADJUDICATED CLEAN (PR #3644); the surprise is real and properly escalated

Both charter targets hit (Deely's 932 MW paper event OUT, Braunig's 477 MW real exit IN), a
third defect found and fixed on the way (the builder now reads the whole committed release
series, not one retired sheet), 5c refusal honoured, rule 27 blob discipline recorded,
no solve, no registration, no matrix contact. **The pre-registered expectation FAILED and
was reported before interpretation, as chartered:** the corrected ERCOT thermal target is
LARGER (1.534 → 2.294 GW) — removing Deely is outweighed by +1.7 GW of physical exits the
old target could not see. The consequential row is **Sandy Creek (56611_S01, 1,008 MW
supercritical coal, OP through RY2024, OS in RY2025)**: carried by the vintage-2020 fleet
basis, retirable by a screen, and never examined by FFR-6A's decode because the old target
lacked it. **Consequence recorded: FFR-6A's V.1(c) bounding finding ("true margin-driven
exit total ≈ 0 GW") is CAVEATED — derived on a target now known incomplete — and must not
be relied on until re-derived (→ FFR-7C).** The unified arm's 10.9 GW false wave is
unchanged; its err_frac improvement is purely the denominator growing and is NOT progress.
Also found, deliberately not fixed (out of charter): the `gas_st`↔`gas_ct` taxonomy seam —
the target can never contain `gas_st`, so no `gas_st` model retirement can ever be credited
in any ISO. On the open queue for an owner card after FFR-7C reports.

### W.2 Rule-22 regime change — owner clarification, acknowledged and operationalized

Commit 06c5971f (session neiso-86, owner clarification 2026-08-06) rewrites rule 22's
posture: **what is held out is the SCORE, never the data or the architecture.** Intake needs
no per-ISO/per-window authorization; measured inputs apply consistently across ALL years;
2020–2022 are ITERATIVE diagnostic touchpoints (diagnose → re-train on 2023–2025 only →
re-test); 2019 is THE one-touch year. Manager duties executed: (a) standing prompt
boilerplate updated — no future prompt carries the old per-window intake-authorization
language; (b) verified the freeze still gates the spend and is ACTIVE (a second owner
lift/spend/re-arm cycle landed 2026-08-06 — the touchpoint loop working as the new text
describes).

### W.3 FFR-7B — IN FLIGHT, adjudication deferred

Arm 1's code is on main (PR #3649: statutory RPS trajectories + eligible sets for
NYISO/NEISO/CAISO, parameter registry citations, byte-identity tests, spec sync) but the
Arm-1 paired-control keeper deltas and the lane handoff are NOT yet committed — the controls
are multi-hour solves; presumed still running. No adjudication until the handoff lands; the
prompt's HOLD-PROMOTION posture governs whatever the controls show.

### W.4 FFR-7C — chartered by the manager (Q.2 test: committed-artifact question, no answer)

Re-derive the exit decode on the CORRECTED target: per-unit margins at measured prices vs
bars for every newly-visible in-window exit (Sandy Creek foremost), via FFR-6A's replica
method, committed artifacts only. Restate the economic-exit bound; report — not re-open —
its implication for the deferred D-21(a). Also report (not decide) FFR-7A §9.3's OP-only
vintage-gate question. Prompt: pack §0s.

### W.5 Queue delta

ADD: the gas_st taxonomy seam (owner card after FFR-7C). CARRY: FFR-3V §6.1 (unowned),
FFR-4D row-4, ruff-autofix/constants.py lint fix, assign_zone_by_coords, pre-existing test
failures, D-21(a) DEFERRED (owner re-opens, not the manager). STRUCK: nothing this cycle.

## Addendum X — Wave 7 closes: the bound survives; Arm 1 zero-delta; the NEISO locked-test record is false

**Written 2026-08-06 by the workstream manager at `origin/main` `97e37b0f`.**

### X.1 FFR-7C — ADJUDICATED CLEAN (PR #3658)

Pre-registration discipline held (unit list + decision rule committed before any margin was
computed; the reproduction gate re-derived FFR-6A's replica exactly). **The restated bound:
ERCOT's margin-consistent exit total 2021–2025 on the CORRECTED target is 0 MW of 2,294 MW**,
decoded unit-by-unit over 87.6 % of the thermal target with per-unit measured heat rates —
every large exit clears its bar at measured prices (Sandy Creek 1.25×, the tightest), and
the taxonomy-seam units were scored against BOTH bars with bar-invariant verdicts. FFR-6A's
conclusions 1 (price object) and 2 (bars exonerated) are VERIFIED UNTOUCHED; the V.1(c)
caveat is DISCHARGED — the bound is restored, stronger, at the larger denominator. **The
evidence-kind finding the manager carries to the owner:** this window can FALSIFY an
over-retiring screen but can never CONFIRM a correctly-retiring one (a correct object must
produce ≈ 0 economic exits here) — any positive validation of a repaired price object must
come from the PRICE side (the 161/217 h > $100 the object misses), not the exit side. This
sharpens what the deferred D-21(a) lane would measure, without re-opening it. Second-order
flag → card D-24: the ERCOT ≥ 300 MW recall gate's two members are Decker (not in the fleet
— unreachable by construction) and Sandy Creek (which a correct screen must NOT retire), so
the gate as constructed is one no admissible screen can pass. The §9.3 OP-only question was
measured and reported: ERCOT essentially invariant (one 7.6 MW row); widening (a) bites
MISO (84 rows / 392.7 MW thermal) — recorded as available, no action recommended now.

### X.2 FFR-7B Arm 1 — ADJUDICATED CLEAN (PRs #3649/#3654); Arms 2–3 handed off correctly

Statutory trajectory + eligible-set corrections landed for NYISO (2040 1.00 → 0.70, PSL
§66-p), CAISO (0.60 flat, §399.15(b)(2)(C)), NEISO (per-state new-renewable blend
.29/.40/.48/.50 replacing the "CES blend") — every level web-verified against primary
statute text, zero free parameters, no gate flag (an ungated rule-14 accurate-data
correction). **The Addendum-D paired controls came back BYTE-IDENTICAL in all three ISOs**
(NYISO 25/25, CAISO 22/22, NEISO 28/28 parquet sha256-equal; registered as verification
runs) — backcast contact NONE, no promotion hold needed. The forecast-side mechanism removed
is exactly FFR-6B §8.3's unstatutory ACP-pinned entry subsidy. In passing the lane found and
fixed THREE pre-existing main breakages, most seriously **nyiso-128's unregistered
cache-key field live on main** (the FFR-5E §6.2 hazard class in the wild: the pinned default
key had moved and every default-key pin test was failing on clean main) — noted as a CI-gap
data point: the pin tests exist but main was red and nothing stopped the merge. Arms 2–3
were HANDED OFF, not landed ("never land a partial arm" honored), with implementation-ready
notes (7B handoff §6) — continuation FFR-7B-2 dispatched (pack §0t).

### X.3 Wave 7 — CLOSED (with one continuation)

FFR-7A, FFR-7B Arm 1, FFR-7C adjudicated clean; FFR-7B-2 (Arms 2–3) is the sole carry-over,
chartered under the same owner decision D-22(a). Registration/matrix hygiene verified on all
three lanes; keepers moved twice mid-wave (NYISO → nyiso-128-solar-basis; CAISO → caiso-175
earlier) with zero shipped-default flips (R.1-checked).

### X.4 The NEISO locked-test record is FALSE — neiso-87's governance finding, verified

Not an FFR lane, but a record the manager's own brief repeats. neiso-87
(`results/calibration/ASSESSMENT-neiso87-declaration-2026-08-06.md` §1) searched the
artifact record at HEAD: **no NEISO 2019 solve, score, bundle, bench row, or registry entry
exists**; the memo cited as authorization contains no mention of 2019; `locked_test_scored_on`
points at a config id whose own record says "solved full-span 2023–2025"; and the 2026-07-07
owner decision authorized a one-shot on 2022 (pre-tier-split terminology) whose execution
was HELD the same day. The third-party peer review reached the same conclusion independently
(§6.3 item 1). **The "SPENT, never re-grantable" claim is documentation drift, live in 13
files including CLAUDE.md rule 22 itself, the marker, and the freeze file.** The correct
framing of any future NEISO `final` question is "should a never-granted one-shot be granted"
— and neiso-87's own merits answer is NOT YET (unrunnable year, non-discriminating test).
Editing a locked-tier marker is an OWNER ACT: card D-23 put. Until signed, the manager's
own briefs stop repeating SPENT and cite this addendum instead.

### X.5 Cards put at this sitting

* **D-23 — correct the NEISO locked-test record** (SPENT → never-granted) across the 13
  files, by a chartered record-correction lane, with the marker edit as the owner's own
  signed act. Manager recommends: sign.
* **D-24 — the ERCOT ≥ 300 MW recall gate** measures something no admissible screen can
  pass (X.1). Manager recommends: redefine it against the reachable set (fleet-carried,
  non-instrument exits) as part of scoring, not chase it.
Dispositions recorded by addendum when signed.

### X.6 Owner signatures (same sitting, 2026-08-06)

* **D-23 — SIGNED: correct the NEISO locked-test record.** The owner's signature here IS the
  authorization for the marker edit (the CAISO-GRANT pattern: a governance lane executes a
  signed owner act against committed artifacts). Charter **NEISO-RECORD**: SPENT →
  never-granted across all 13 files (marker `locked_test`/`locked_test_note`, `final._note`,
  CLAUDE.md rule 22's "NEISO is the latter" clause, holdout-freeze.json, the 2022 touchpoint
  sidecar, matrix doc, calibration-log entries, second-hand handoff/audit repeats), every
  edit citing neiso-87 §1 + peer review §6.3 + this signature. The correction GRANTS
  NOTHING — neiso-87's merits answer on `final` (NOT YET) stands untouched.
* **D-24 — SIGNED AS RECOMMENDED (after owner clarification, re-put with the
  couldn't/wouldn't decomposition): redefine the ≥300 MW recall gate against the reachable
  set** — members = fleet-carried units whose exit was economic or vintage-visible-
  instrument-driven; empty set reports n/a, never 0/N. Charter **SCORE-GATE** (small,
  scorer-only).
Both prompts: pack §0t addendum. FFR-7B-2 (already in §0t) dispatches alongside them.
