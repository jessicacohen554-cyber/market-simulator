# PRECOMMIT — ercot-204: (A) the published-RTORPA admissibility gate, (B) the rule-26 `[R-DELETE]` successor

**Pushed BEFORE any solve.** Part A is a read-only Phase-0 gate whose measurement
is already complete and is reported here at full magnitude; Part B is the A/B
whose construction, kill gates, retention evictions, DOF claim and
direction-blind decision rule are fixed here and are **not renegotiated after
measurement**.

Keeper at session start, verified at this session's HEAD from the **committed
record** (`meta.json` `coal_prb_sigmoid_overrides` **and** the resolved
`run_config.json` `scenario_config`, rule 24 `[R-REGISTRY]` — never
`scenarios.py` defaults):
**`2026-08-14-ercot202-arm-plantphysics`**, bundle
`results/calibration/ercot202_plantphysics_B` — determination **NOT-YET**, fail
set **{C3a-2023, C3b-2023}**, C3c the single ledgered **CAVEAT ×3**.

---

## 0. Shorthand, scope, fences

### 0.1 Shorthand

This session is **ercot-204**, the shorthand the ercot-203 lane declared for its
successor. Noted and **not renamed** (it is an owner call): `main` carries a
**duplicated `## ercot-202` heading** in `docs/calibration-log/ercot.md` — one at
line 8063 (the owner sitting record) and one at line 8212 (the T-1 non-viability
entry) — and the 198–205 shorthand ledger is tangled across parallel branches
(ercot-203b's own collision note documents two lanes taking `ercot-203`
simultaneously). 197/199/200 are unspent. Nothing is renamed here.

### 0.2 Scope fences (binding, and none of them are mine to reopen)

* **Q-B (FINAL)** — no ERCOT C3a-2023 backcast spend of any kind. 2023 movement
  is side-effect-reported at full magnitude under the card-R ceiling and is
  **never** a basis.
* **R-A** — NOT-YET stands as ERCOT's public claim; no C3b-2023-targeted
  determination rounds.
* **T-4 refused; T-2 behind the D2 freeze; T-3a is a rubric change, owner-only.**
* **L-SCAR tightness identification is DO-NOT-REDO** (V0 adjudication,
  ercot-195). Part A's structural measurement stops at *measurement* and
  charters nothing — see §1.4.
* **Rule 22 `[R-HOLDOUT]`** — ERCOT holds **no** `complete` and **no** `final`
  marker. Only {2023, 2024, 2025} are solved, scored, read or registered; no
  `--holdout-authorized`, no marker sought, granted or spent.
* **Rule 25 `[R-ISO-SCOPE]`** — ERCOT only. No other ISO's shard, keeper,
  registry or bench is read for edit or written.

---

# PART A — the chartered lever: **NON-VIABLE ON PREMISE**

## 1.1 What was chartered, and the discipline that was applied first

The dispatch chartered *"the single overlay-completeness delta"*: complete the
2024 published-adder overlay by adding the missing published **RTORPA**
(+0.237 $/MWh dw, ercot-198), justified as a **measured-input completeness
repair** under rules 13/14.

The dispatch also ordered the **T-1 discipline** — *verify the keeper's ACTUAL
effective values from the committed record before chartering anything* — because
the last signed ERCOT lever died on an unverified premise. That verification was
performed first, and **it falsified this charter's premise too**, for a different
reason than T-1's. Probe:
`scripts/probes/ercot204_rtorpa_admissibility.py` →
`results/calibration/ercot204_rtorpa_admissibility.json`. No LP, no year solved
or scored.

## 1.2 The three gates, decided direction-blind and before any residual

**G1 — ARMED STATE (read from the resolved `run_config.json`).**

| field | keeper value |
|---|---|
| `ercot_ordc_total_reserve` | **True** |
| `energy_reserve_coopt` | **True** |
| `ordc_multistep_floor` | **True** |
| `ercot_multiproduct_as_coopt` | **True** |
| `ercot_rtordpa_overlay` (calibration flag) | **True** |
| **any `*rtorpa_overlay*` channel** | **DOES NOT EXIST** |

The model's RTORPA counterpart is **armed**: the LP enforces the published ORDC
total-reserve demand curve and **its dual *is* the model's RTORPA** (sidecar
`ordc_adder`). The chartered delta is not a flag that is off — it is a channel
that does not exist and would have to be built.

**G2 — rule 19 `[R-ONE-MECH]`.** Building it stacks a **second** mechanism for
one phenomenon on the **unexplained residual of an armed first** — the precise
construction rule 19 forbids. Independently adjudicated on `main` **today**:
ercot-203b (2026-08-15) filed the RTORPA item as *"a **mechanism** question about
the co-optimized reserve dual, not overlay completeness, and rule 19 bars
overlaying the published series on top of the mechanism meant to produce it."*

**G3 — rule 13 `[R-MEASURED]` forward-analogue test**, the charter's own cited
justification, applied to the charter: *"could this same quantity be produced for
a forward year from forward drivers, and would it respond to changed
conditions?"* **No.** RTORPA is not an independent market datum — it is a
deterministic function of realized reserve levels through the published ORDC
curve (`adder = LOLP(R) × (VOLL − λ)`, Nodal Protocols §6.5.7.3). **Its forward
analogue *is* the endogenous computation the model already performs.** Overlaying
the measured 2024 series would substitute a measured **outcome** for the
mechanism under validation, in hours the model's own reserves do not price —
the forbidden half of rule 13, not the permitted one.

**The asymmetry that makes this a rule and not a preference.** RTORDPA *is*
armed as an overlay and is correct to be: it prices **discretionary out-of-market
RUC/ECRS deployments**, an operator action with **no endogenous counterpart** in
the model. RTORPA has one, armed. One overlay is admissible and the other is not,
for a stated structural reason rather than a fit reason.

**VERDICT: NON-VIABLE ON PREMISE. No lever is substituted** (dispatch standing
instruction), no `ScenarioConfig` field is added, no A/B is pre-registered for
Part A, and no cell verdict changes — no mechanism was tested.

## 1.3 What was measured anyway, reported at full magnitude

Re-measured on the **current** keeper rather than inherited from run192.
ercot-198 reproduces exactly where the bases agree:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| published RTORPA dw $/MWh | 1.2675 | **0.2368** | 0.0787 |
| published RTORPA non-zero hours | 1,705 | **560** | 253 |
| endogenous `ordc_adder` dw | 0.4067 | **0.0000** | 0.0000 |
| `ordc_adder` non-zero hours | 42 | **2** | 1 |
| `rtordpa_overlay` vs published RTORDPA, max abs diff | 4.6e-13 | 2.8e-14 | 1.4e-14 |

Two basis caveats, stated rather than buried: (a) this probe reports the **raw**
NP6-905-CD archive, while ercot-198 applied a settlement-closure guard rejecting
one uncorrected print (2025 h4334, archive $414.12/h against a settled hub RTSPP
of $54.96) — that single hour is the entire 0.0787-vs-0.015 distance in 2025;
2024 is unaffected. (b) Neither number changes the gate, which turns on
**admissibility, not magnitude**.

## 1.4 THE OBJECT THE GATE LEAVES STANDING — measured, handed over, NOT chartered

**The armed endogenous mechanism is not broken.** In 2023 it fires in 42 hours at
up to $1,920/h, and **all 42 fall inside** the 1,705 hours the published RTORPA
priced (overlap 42/42), with the model's held ORDC-total reserve within **0.2 %**
of published RTOLCAP (8,122 vs 8,108 MW).

In 2024/2025 it reads ~zero across 560/253 published-fired hours — and **the
simplest explanation is falsified**: the model does not see a comfortable system.
It holds materially **less** reserve than the real one did (2024 **6,955 vs
8,854 MW**; 2025 **6,638 vs 9,654 MW**) and still does not price, while its own
ORDC-total row records non-zero shortfall in **40** (2024) and **4** (2025) of
those hours.

*Caveat, stated:* the model family's `held_mw` and published `RTOLCAP` are
constructed differently and are **not an identity** — the comparison is
indicative of where each system's reserve sits, not a like-for-like
reconciliation. It is reported because it **falsifies** the simplest explanation,
not because it identifies anything.

**Where the ORDC pricing region sits relative to the model's reserve
representation is therefore the open object.** It is a mechanism question, it is
**handed to the owner un-chartered**, and this session prepares no lever on it —
the adjacent L-SCAR tightness identification is **DO-NOT-REDO**.

---

# PART B — the pre-authorized fallback: the rule-26 `[R-DELETE]` successor

Authorized by the dispatch verbatim: *"Rule 26 `[R-DELETE]` successor already
NAMED by the current keeper and available as a smaller second item if this lane
stalls."* The lane stalled on premise (Part A), so Part B executes. **This is not
a lever substituted on my own authority** — it is the named second item, and it
adds no mechanism and no degree of freedom.

## 2.1 The obligation, and why it was deferred rather than discharged

`docs/PRECOMMIT-ercot202-…` §2/§7 bound the promoting commit to delete the
transitional flag and the pre-repair branch. The promotion did not, and its
recorded reason is **measured, not preferential**: `ScenarioConfig.with_overrides`
is `dataclasses.replace`, which **raises on an unknown key**, and this keeper's
`meta.json` carries `ercot_faststart_pool_plant_physics: True` inside
`coal_prb_sigmoid_overrides` (the `prb_overrides` replay channel) — verified this
session. Deleting the field without a re-solve makes the **keeper unreplayable**
and breaks every future control and re-gate.

The successor named by that note is therefore: **delete the field and the
pre-repair branch, make plant grain unconditional, AND RE-SOLVE so no bundle
references the flag.**

## 2.2 The construction — a deletion, not a mechanism

* `config/scenarios.py` — remove the field (`:8182`), its cache-key registration
  (`:883`, `:1175`) and its tier tag (`:13197`).
* `data/fleet/offer_surfaces.py` — both pool bodies (stepped `:2881`, `contpct`
  `:3075`) compute `plant_md` **unconditionally**; the retained pre-repair
  row-grain branches (`:2913`, `:3103`, live only under `plant_md is None`) are
  **deleted outright**, not zeroed (rule 26: deleted means deleted); the
  provenance labels (`:2989`, `:3138`) lose their dead "row (pre-repair,
  vacuous)" arm.
* **Zero fitted scalars. Zero new fields.** `FASTSTART_POOL_MIN_DOWN_HOURS = 2.0`
  is untouched; no band, composition, ladder or boundary moves.

## 2.3 PREDICTION, falsifiable, fixed before the solve

**P-1. The re-solve reproduces the keeper BYTE-IDENTICALLY on all 12 hourly
sidecars.** The armed path is the keeper's path; making it unconditional removes
only the dead branch. *Falsifier: any sidecar differs.* A falsified P-1 means the
deletion was **not** behaviour-preserving — this session then **stops, reports,
and registers the result unrewritten**; it does not adjust the deletion until it
matches.

## 2.4 KILL GATES — live, direction-blind, not renegotiated after the solve

Baselines are the keeper's own committed artifacts (no solve produced them):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| C3a (rubric) | FAIL −33.2 % | PASS −0.8 % | PASS −7.5 % |
| C3b (rubric NRMSE) | FAIL 0.604 | PASS 0.135 | PASS 0.096 |
| C3c model tail >$200, max-zonal (actual) | 58 (181) | 22 (53) | 1 (31) |
| shed hours | 4 | 1 | 0 |
| spurious mid-band | 9 | 11 | 0 |
| coal above product ceiling (TWh) | 0.1213 | 0.1838 | 0.1095 |

* **G-REPRO — PRIMARY.** The re-solve is byte-identical to the keeper on all 12
  hourly sidecars. This is simultaneously the deliverable and the proof that the
  deletion changed nothing.
* **G-SHED.** Shed hours **4 / 1 / 0** must not rise in any year.
* **G-C3c.** Ledgered max-zonal tails **58/181, 22/53, 1/31** must not move away
  from actual in any year.
* **G-COAL148** (carried live). Coal above the measured product ceiling may not
  rise more than **+0.5 TWh** in any year. Screened by construction — no coal row
  is touched — so any non-zero move **falsifies that claim**.
* **G-SPUR.** Spurious mid-band **9 / 11 / 0** must not increase.
* **G-OWNER.** **C3a-2024 and C3a-2025 keep PASS**; **C3b-2024 ≤ 0.20**.
* **G-DOF.** **Zero** fitted scalars; `n_entries 18` / `n_residual 6` unchanged.
  Satisfied by construction — a deletion cannot add a degree of freedom. **A
  field is REMOVED, so the registry surface shrinks.**
* **G-D2.** No **new** D-4 FAIL row versus the keeper. The pre-existing
  `reliability_floor × CT_PEAKER` h14-21 condition is carried, not introduced.
* **Rule 22 LOYO** — structurally N/A and stated as such: the change is
  year-agnostic and P-1 asserts byte-identity in **all three** years, which is
  the held-out evidence (it cannot buy in-sample gain anywhere).

**Failing any live gate ⇒ REJECTED-AS-ARMED, reported at full magnitude and not
rewritten.**

## 2.5 The ADVERSE branch, written out before the solve

If **G-REPRO fails** — the deletion is not behaviour-preserving — then the
retained pre-repair branch was reachable on the keeper's own armed path, which
would be a **finding about the keeper**, not a defect in the deletion. In that
case: **stop, register the result as measured, do not repair the deletion into
agreement, and escalate.** The mechanical verdict stands unrewritten either way.

Per rule 1 `[R-STRUCT]`, a worse residual is **never** grounds to restore a dead
branch; and per the direction-blind rule below, a better one is never the reason
to delete it.

## 2.6 DECISION RULE — direction-blind, fixed here

The recommendation reads **only** (a) each live kill gate's PASS/FAIL and (b) the
LOYO disposition. It does **not** read the sign or size of any C3a, C3b or C3c
movement.

* **All live gates PASS ⇒ RECOMMEND PROMOTION** — on rule-26 discharge alone. **No
  metric gain is claimed and, if P-1 holds, none exists by construction.**
* **Any live gate FAILS ⇒ DO NOT RECOMMEND.** Record REJECTED-AS-ARMED and
  escalate per §2.5.

**The keeper cannot change in-session** (dispatch): this session reports a
promotion **RECOMMENDATION** only, and edits no keeper shard.

## 2.7 Bookkeeping

* **Rule 15 `[R-DASHBOARD]`** — the run is registered, committed and pushed in
  **this** session whatever the outcome; the FINDING and dashboard carry the
  result, not chat. If it is recommended as keeper, its `hourly/` sidecars are
  committed.
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025, one bundle. Years run
  **sequentially**; per rule 12 they may be chained as per-year invocations
  (`--years` + `--reuse-solved`) because a single ERCOT per-plant year already
  needs most of this 15 GB box — **never in parallel**.
* **Retention (top-15 per ISO), evictions named EX ANTE.** ERCOT stands at
  **15** registered runs with exactly one protected
  (`2026-08-14-ercot202-arm-plantphysics`, the keeper). Registering **one** run
  displaces the **single oldest unprotected** run —
  **`2026-08-08-run178-continuous-grain`** — named here before the fact and
  subject to `dashboard_add_run.py`'s own protected-set check.
* **Rule 27 `[R-PUSH]`** — `scenarios.py` and `offer_surfaces.py` are ≥300-line
  core files and **will** be edited. Edits are made locally with the Edit tool,
  the exact on-disk bytes are pushed, and each blob is verified against the
  remote (line count + hash) before the next commit. No bulk rewrite from
  regenerated response content. No push runs while a solve runs.
* **Rule 28 `[R-MECH-MATRIX]`** — duty (a) DO-NOT-REDO checked before this
  document (Part A tests no cell; `ercot_rtordpa_overlay` stays **K**, read
  only). Duty (b) the `ercot_faststart_pool_plant_physics` cell is re-stamped in
  the **ERCOT shard only**. Duty (c) **a field is removed, not added** — the base
  row and every shard's cell line are retired in the same PR, and
  `check_mechanism_matrix.py` must exit **0**.
* **No PR** (dispatch: push-and-stop; the owner merges). **No new GitHub Actions
  workflow** — all work in-session.

## 2.8 What this session does NOT claim and does NOT touch

* **No claim on C3a-2023 or C3b-2023.** Movement — if P-1 holds there is none —
  is reported at full magnitude and is never a gate, target or basis.
* **No C3c ledger change, no rubric amendment.** The CAVEAT ×3 stands.
* **No holdout marker granted or spent. No mechanism added.** Part A adds
  nothing; Part B removes.
* **INHERITED NAMED PERMANENT LIMITATION (ercot-188/E2, unexpired):**
  `ercot_econ_curve_top_refine` writes heat rates into the P0 objective on this
  keeper, so the offer-surface family's **P0 bit-identity proof stays forfeited**.
  Stated so no byte-identity result in Part B is over-read beyond what it is: a
  whole-solve reproduction, not a seam proof.

**Next shorthand: ercot-205.**
