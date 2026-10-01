# FINDING — ercot-213 (RESERVE-BASIS-2, card X item X-3 second increment): the anchoring repair WORKS — G-CAP passes with zero violations and the ercot-212 super-VOLL defect is gone — but the arm is **REJECTED-AS-ARMED** on the same G-SPUR kill, now sharper

**Session ercot-213, 2026-08-16, branch `claude/ercot-reserve-anchoring-fix-p6c55p`.**
Precommit (pushed before any solve):
`docs/PRECOMMIT-ercot213-published-anchor-2026-08-16.md`. Keeper at session
start AND end: **`2026-08-15-ercot204-rule26-delete`** — unchanged and
protected throughout; the keeper cannot change in-session (X-3), so the
outcome below is a promotion RECOMMENDATION only.
Runs registered: **`2026-08-16-ercot213-ctl-headbase`** /
**`2026-08-16-ercot213-arm-pubanchor`** (both with payloads, rule 15).
Probes: `results/calibration/ercot213_ab.json`,
`ercot213_anchor_gates.json`, `ercot213_coal148.json`,
`ercot213_headdrift.json`, and the environment-sensitivity pair
`ercot213_*_lockenv.json`.

## 0. VERDICT

**The repair is CONFIRMED to repair what it was built to repair, and the arm
still fails.** Both halves are load-bearing and neither cancels the other:

* **G-CAP PASSES with ZERO violations in all 26,280 solved hours.** The
  ercot-212 arm's diagnosed defect — a written `ordc_adder` of **$10,000/h =
  2 × VOLL**, a price the published protocol cap (`λ + adders ≤ VOLL`) makes
  unreachable — is **gone**. The armed maxima are now **$4,701.14 (2023) /
  $2,049.45 (2024) / $1,196.56 (2025)**, and the 2023 maximum lands at
  λ $298.86 + adder $4,701.14 = **exactly $5,000.00 = VOLL**: the cap binds
  and holds rather than being exceeded. The ercot-212 §5 diagnosis is thereby
  confirmed constructively, not merely argued.
* **G-SPUR KILLS, and by MORE than it killed ercot-212**: 2023 spurious
  mid-band hours **9 → 17 (+8)** against the pre-registered +5 bar (ercot-212
  read 9 → 16, +7). Under the precommit §4 direction-blind rule, one kill ⇒
  **REJECTED-AS-ARMED**; the verdict is mechanical and stands unrewritten.

**Why fixing the anchor made G-SPUR WORSE, which is coherent rather than
paradoxical.** G-SPUR counts hours with model price in **[150, 500]** while
actual < $150. The repair's whole effect is to *lower* adders — hardest where
λ is largest, since the rescale factor is `(VOLL − λ)/VOLL` (≈0.99 in a
$30/MWh hour, ≈0.40 in a $3,000/MWh hour) — and to drop the fast tier's
contribution outright. Hours the ercot-212 arm pushed clear **above** the
$500 top of the spurious band are pulled back **into** it. The mis-anchoring
was real and is fixed; the mid-band spill it was masking is a **different**
defect, and this session isolates it rather than removing it.

## 1. THE GATE TABLE (full magnitude, control → armed, pinned environment)

Measured control-vs-armed, both members solved at the same tree (`7246272`)
on the keeper's TRUE solve environment (highspy 1.15.1 / pandas 3.0.5 /
pyarrow 25.0.1 — recorded in both bundles' `meta.environment`), full span
2023+2024+2025 sequential in one invocation each (rule 12).

| gate | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| **G-REPRO′** | control reproduces the keeper's determination EXACTLY (§3) | | | **PASS** (as amended) |
| G-SHED (no increase) | 4 → **0** (h5490/5682/5802/5994 all clear) | 1 → 1 (h3067) | 0 → 0 | **PASS** (reductions reported) |
| G-C3c (not away from actual) | 57 → **123** (181) | 22 → **33** (53) | 1 → **3** (31) | **PASS** — toward actual in every year |
| **G-SPUR** (≤ +5) | 9 → **17 (+8)** | 11 → 13 (+2) | 0 → 0 | **KILL** |
| G-SPAN (≤ 2.0 %) | max 0.077 % (CT_PEAKER) | 0.0 % | 0.0 % | PASS |
| G-COAL148 (rise ≤ 0.5 TWh) | 0.0 | 0.0 | 0.0 | PASS |
| G-OWNER | — | C3a-2024 PASS, C3b-2024 PASS | C3a-2025 PASS | PASS |
| G-DOF | `n_entries` 8 / `n_residual` **6** → 8 / **6**, identical | | | PASS |
| G-D2 | D-4 FAIL set IDENTICAL (the 3 pre-existing `reliability_floor × CT_PEAKER` h14-21 rows; no new row) | | | PASS |
| **G-CAP** (added, §3) | max adder **$4,701.14** @ λ $298.86 → λ+adder = **$5,000.00** | max **$2,049.45** | max **$1,196.56** | **PASS** — 0 violation hours / 26,280 |

**LOYO:** structurally N/A as pre-registered (parameter-free rule, nothing
identified on any year); per-year deltas stand in its place, above.

**G-DOF note, reported not buried.** Both members read `n_entries` **8**
against the keeper attestation's recorded **18**. That is **HEAD drift in the
ledger BUILDER, not an effect of this delta**: re-running
`build_dof_ledger.py` at HEAD on the KEEPER's own `run_config.json` (in a
scratch copy — the committed keeper bundle was NOT modified) also yields
8 / 6. What G-DOF actually tests is unchanged and passes: control and armed
are identical, and `n_residual` stays **6**.

## 2. THE ADDER CENSUS — the repair measured directly (`ercot213_anchor_gates.json`)

| quantity | 2023 ctl → arm | 2024 ctl → arm | 2025 ctl → arm |
|---|---|---|---|
| `ordc_adder` nonzero h | 42 → **564** | 2 → **178** | 1 → **67** |
| … > $1 | 3 → **184** | 0 → **37** | 0 → **7** |
| … > $100 | 2 → **117** | 0 → **16** | 0 → **3** |
| max written adder | $1,920.20 → **$4,701.14** | $0.15 → **$2,049.45** | $0.03 → **$1,196.56** |
| λ at that maximum | $330.62 → $298.86 | $100.51 → $238.90 | $69.44 → $214.30 |
| published settled (h>$1 / h>$100) | 294 / 17 | 78 / 4 | 14 / 0 |

**The netting's identification reproduces exactly** (ercot-212 §5 predicted
175/45/5 h ≥ $1 and an upper bound 571/190/67 nonzero): measured
**184/37/7 h > $1** and **564/178/67 nonzero**. The incidence half of the
ercot-212 identification is now validated a second time, on a differently
priced arm.

**The landing zone MISSED, and this is the honest report.** The precommit §2
and the dispatch both stated an expected 2023 deep tail of **~20–37 h > $100**
against 17 published settled. Measured: **117**. The prediction came from the
Phase-0 **out-of-LP** construction, which evaluates the adder at the *cap*
(`min(10,700, RTOLCAP+RTOFFCAP)`); the LP's realized marginal reserve level
sits **below** the cap whenever physical headroom is tighter than telemetry,
and the netting itself frees held reserve into energy, lowering the level
further. So the LP prices deeper than the out-of-LP mirror anticipated — a
measured limitation of that mirror, named here so no future session re-derives
a landing zone from it without this correction. **§2 predictions were never
gates** (only §3 is), so this does not itself change the verdict.

**The floor limitation the precommit named up front is confirmed immaterial.**
The rescale under-states an OBDRR048 floor step by `λ/VOLL`. In the writing
hours the armed member's total-family held reserve has p50 **6,658.8 (2023) /
5,724.4 (2024) / 5,594.9 (2025) MW**, i.e. inside the ≤7,000 MW floor region
— but at those levels the armed LOLP curve prices ~$200+, an order of
magnitude above the $10/$20 floor steps, so the floor never sets the marginal
step and the under-statement never binds.

## 3. G-REPRO′ — the control, the keeper, and the drift (§3 clause (c))

The keeper is **not byte-reproducible at HEAD**: 0 of 12 hourly sidecars match
(ercot-212 Amendment 1 measured 1 of 12 differing on this environment; the
tree has advanced since). The drift is **score-inert on the determination**:

| | keeper | control (pinned) |
|---|---|---|
| C3a-2023 | −33.2 % | **−33.2 %** |
| C3b-2023 | 0.604 | **0.604** |
| C3c tails | 58 / 22 / 1 | **58 / 22 / 1** |
| shed hours | 4 / 1 / 0, same hour lists | **identical** |
| spurious | 9 / 11 / 0 | **identical** |
| mean price | — | −$0.000 / −$0.075 / −$0.026 /MWh |
| max class energy | — | 0.297 / 0.445 / 0.463 % |

The official scorer reproduces the keeper's determination on the control
exactly: **NOT-YET, fail set {C3a-2023, C3b-2023}**, C3c failing all three
years. So the A/B's control-vs-armed basis is sound and the delta below is the
mechanism, not the drift.

**A second, independent reproduction: the ENVIRONMENT IS IMMATERIAL HERE.**
An earlier full A/B of the identical delta ran on the LOCKFILE environment
(highspy 1.14.0 / pandas 3.0.3 / pyarrow 24.0.0) and reproduces the pinned
pair's gate table **to the last decimal** — every C3a, NRMSE, spurious count,
tail count, shed hour list, class-energy delta, adder census entry and
G-COAL148 figure is identical. Retained as `ercot213_*_lockenv.json`.
*Why that run exists, disclosed not buried:* the dispatch's environment pin was
reverted mid-session by the repo's own `.claude/hooks/ruff-autofix.sh`
PostToolUse hook, which runs `uv run ruff` — and `uv run` re-syncs
`$CLAUDE_PROJECT_DIR/.venv` to `uv.lock` before executing, so every Edit/Write
after the pin silently undid it. The ercot-204 §B.2 trap arriving through a
hook rather than a typed `uv run`. Fixed by solving from an isolated venv
outside the project directory. **Standing note for every future session that
pins a solve environment in this repo: `.venv` is not a safe place to pin.**

## 4. SIDE-EFFECT REPORT AT FULL MAGNITUDE (Q-B/R-A phrasing — reported, never a basis, never spent)

Standing rulings **Q-B FINAL** (DECISION-CARD-ercot189) and **R-A**
(DECISION-CARD-ercot193) are cited and honoured: the numbers below were never
targeted, are not gates, are not a promotion basis, and the §4 decision rule
never consulted them. On the official scorer
(`scripts/calibration_verdict.py`, committed artifacts only):

* **C3a-2023: −33.2 % → +0.4 %**, and C3a **PASSES all three years** on the
  armed member (the control FAILS 2023). The magnitude falls 32.8 pp.
* **C3b-2023: 0.604 → 0.203**, against the 0.20 bar — **still FAIL**, by
  0.003.
* **C3c-2023 (123/181) and C3c-2024 (33/53) now PASS their bands**; the keeper
  carries both as ledgered caveats at 58/181 and 22/53. **C3c-2025 still FAILS
  (3/31).**
* Armed fail set **{C3b-2023, C3c-2025}**; determination **NOT-YET** on the
  **C6 UNATTESTED** governance gate — no attestation is generated for an A/B
  pair (the same condition ercot-212 recorded).
* DA diagnostics on the armed member: 2023 −18.4 % vs DA, 2024 −0.1 %,
  2025 −9.6 %.
* Dispatch: 2023 load shed **vanishes** (4 h → 0), as the precommit predicted
  — freed reserve serves load. Volume effects are the netting's alone; the
  anchor is post-solve and moves no MW.

**No C3a-2023 or C3b-2023 improvement is claimed, and none is spent.**

## 5. PROMOTION: **NOT RECOMMENDED** — and what the owner is actually being asked

**Recommendation: do NOT promote `2026-08-16-ercot213-arm-pubanchor`.** The
mechanical rule kills on G-SPUR, and the owner's standing structural standard
("structural integrity outranks gate regression") is judged **NOT** to rescue
it — not because the arm is structurally wrong (it is now structurally
**right**: G-CAP proves the published protocol cap holds, the counterpart is
single, the anchor is the published one, and zero scalars were fitted), but
because **a mid-band price defect that the arm makes measurably worse is not
cured by the arm being right about the anchor**. Promoting would trade a
protective gate for load-bearing gains the standing rulings forbid using as a
basis.

**What this session establishes for the next one, stated plainly:** the
reserve-basis object is now split cleanly in two, and only one half remains
open.

1. **SETTLED — the additive price FORM.** Netting (ercot-212) + published
   `(VOLL − λ)` anchoring + single counterpart (ercot-213) is the correct
   construction, carries zero fitted scalars, and satisfies the protocol cap
   by measurement rather than by argument. It should be treated as the
   standing form of the cap-additive regime; **the bare netting without it
   remains adjudicated `R` (28a) and must not be re-run.**
2. **OPEN — the mid-band [150, 500] spill (G-SPUR).** 2023's +8 is now the
   sole obstacle. It is NOT the anchoring, NOT the counterpart, and NOT the
   protocol cap — all three are fixed and G-SPUR still moves the wrong way.
   The next lever must be identified against the spurious hours themselves,
   and this session deliberately does not guess at it: no candidate is armed,
   no parameter is proposed, and the C3a/C3b/C3c movement above is not
   evidence about the spill.

**Increment (c) is NOT BUILT, per the precommit.** The published two-basis
form (half-hour LOLP term at the online tier, floor keyed to online) was
pre-registered as a second increment "only if the first lands clean". The
first did not land clean, so (c) was not built — building it now would stack a
family-splitting construction on an unresolved kill and confound the two.

## 6. ROSTER — the pair is REGISTERED AND RETAINED, and this differs from ercot-212 on purpose

Both members are registered with payloads (rule 15) and **kept on the site**.
ERCOT's registry: keeper + 2 = **3 runs, no eviction** — exactly the "live
A/B" case the precommit §5 named ex ante.

**This is a judgment call, flagged for the owner rather than made quietly.**
The owner's retention criterion (`keepers/ERCOT.json` `site_retention_note`)
prunes a run "REJECTED WHOLESALE after [the keeper] as offering **no new
mechanism for closing the C calibration gates**". This pair does not meet that
test: it moves **C3a-2023 from FAIL to PASS**, brings **C3b-2023 to within
0.003 of its bar**, and puts **C3c-2023 and C3c-2024 inside their bands** —
and it does so on a construction whose protocol-cap correctness is now
measured. It fails ONE protective mid-band gate. The ercot-212 pair was pruned
on a different footing: it was declined because it was structurally **wrong**
(super-VOLL prices the market design cannot produce), which is what
"wholesale" means. **REJECTED-AS-ARMED ≠ rejected-wholesale**, and the
distinction is exactly structural correctness. If the owner reads the
retention directive more strictly, the prune is one command
(`scripts/prune_iso_runs.py --iso ERCOT`) and this finding remains the durable
record either way.

## 7. AN UNRELATED STOP-THE-LINE DEFECT THIS SESSION FOUND AND FIXED ON MAIN

`main` at `7c723fa` **could not solve any calibration year, for any ISO.** The
nyiso-140 landing (`3febd5c`, PR #4026) added
`reliability_floor_plant_exclusions` to `solve_and_persist` and passes it to
`run_year(...)`, but never added the matching parameter to `run_year` in
`scripts/run_calibration.py`; every `solve_and_persist` call raised
`TypeError` on the first year, before any LP was built. The mechanism's own
tests are solve-free, so nothing in that landing exercised the path — this
session's first replay after the merge was the first solve to touch it.
Repaired in `7246272`, mirroring the sibling `reliability_floor` /
`reliability_floor_overrides` idiom exactly (parameter defaults to `None`;
applied via `config.with_overrides` only when explicitly passed), so
nyiso-140's arming semantics and its "default off, every existing bundle of
all six ISOs byte-identical" claim are untouched. `test_reliability_floor.py`
passes. **Both ercot-213 members solved at that repaired tree.**

## 8. GOVERNANCE

Q-B FINAL and R-A cited and honoured: every 2023 number in §4 is side-effect
reporting; the §4/§5 decisions never consulted residual direction (the
mechanical rule killed on G-SPUR; the promotion decline rests on the
protective gate, and the retention decision on structural correctness).
ercot-206 B0 honoured — no LOLP-table arming in any form; the published
NP6-576-ER table was not read this session. ercot-211 Door A honoured — no
conduct object touched. V0/ercot-201 DO-NOT-REDO honoured — no
tightness-conditioned identification, no E1 term; RTOLCAP entered only as the
already-armed supply-cap construction (FFR-8B §4). 28a honoured — the bare
net-credits arm was NOT re-tested; it appears here only WITH the anchoring
fix. Rule 22: {2023, 2024, 2025} only, no marker sought, no out-of-training
year solved or scored. Rule 25: ERCOT only. Rules 5/13/20/23: zero fitted
scalars — VOLL is the registered `ordc_voll` (read prb_overrides-first), λ is
the LP's own demand-weighted energy dual, the counterpart is an LP dual, both
flags are booleans; `ordc_voll=None` under the armed flag is a loud
`ValueError`. Rules 5/24: both fields registered and recorded in `meta.json`;
no env-var knob, no off-registry channel. Rule 27: edits local, exact on-disk
bytes pushed, ≥300-line pushed files blob-verified. Rule 28: 28b cell verdict
on `ercot_multiproduct_as` + the 28c leg registration land with this finding;
`check_mechanism_matrix.py` exit 0. No new workflows, no cron, solves ran
in-session. No PR (push-and-stop; the owner merges).

**Session consumed the ercot-213 shorthand. Next shorthand: ercot-214**
(ercot-199 remains unclaimed).
