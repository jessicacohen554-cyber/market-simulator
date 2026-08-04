# FINDING — pjm-155: the PJM lane is PARKED PENDING OWNER. Both live items are owner decisions; the dispatch carried no owner answer.

**Verdict: PARKED. Zero LP built, zero solves launched, zero bundles produced,
zero runs registered, zero mechanisms armed, zero cell verdicts moved, zero years
touched outside 2023–2025. Keeper UNCHANGED and re-verified from committed
artifacts alone.**

This session ran **Lane B** of the `pjm-155-owner-decision` dispatch. Lane A1
(`state_carbon_pricing`) and Lane A2 (the G-20b memo sign-off) are both
owner-gated, and **neither was answered in the dispatch**. The dispatch's own
instruction for that case is explicit: do not invent a lever, do not re-solve to
look busy, do not re-open a terminal item — re-verify, record, stop.

*(Session numbered **pjm-155**. `docs/calibration-log/pjm.md` read "Next
shorthand: pjm-154", which is **stale**: the `pjm-154` label was consumed by the
merged `claude/pjm-154-cross-iso-queue-5e2frp` dispatch (PRs #3516/#3520), which
hit the same missing-owner-answer condition, routed its Lane B to MISO, and
logged there as **miso-127** — so nothing was written back to `pjm.md`. Same
spent-label pattern pjm-153 handled, nyiso-121 precedent.)*

---

## §1 — What was re-verified (all no-LP, committed artifacts only)

| Check | Instrument | Result |
|---|---|---|
| Keeper determination | `scripts/calibration_verdict.py --run-id 2026-08-04-pjm-152-collapse` | **CALIBRATED**, 9/9 criteria PASS, **zero FAILs, zero CAVEATs** |
| C1 free-class coverage | same, D-10 line | **all 16/16 · free 12/12** (pinned: `CC_CHP`, `ST_CHP`) |
| C8 grounded rows | same, notes block | 4 rows — `CT_PEAKER` 2023/2024/2025 (16.2/16.4/16.7 %), `ST_GAS` 2025 (39.9 %) — **clean PASSes** under rule 21's grounded-pass clause, D-4 clear, profile r 0.927/0.962/0.974/0.896, CV 0.719/1.075/0.836/2.242. **Not caveats.** |
| Keeper-shard integrity | `scripts/audit_keepers.py --iso PJM` | **PASS, 0 failures, 0 warnings** (keeper + holdout + marker + status all clean; M1 re-key check clean) |
| Marker state | `frontend/data/backcast/calibration-complete.json` | PJM in **`complete`** (declared 2026-07-31, `keeper` correctly re-keyed to `2026-08-04-pjm-152-collapse`); **`final` contains only `_note` — EMPTY for every ISO** |
| Freeze state | `frontend/data/backcast/holdout-freeze.json` | **`active: true`**, declared 2026-07-25, **HELD 2026-07-26** (adopt-and-hold on the CAMPD economic-layup residual) |
| Freeze enforcement | `scripts/run_calibration_full.py:7578-7587` | freeze is read **BEFORE** the marker and **fails closed** — it outranks both `--holdout-authorized` and the `complete` marker |
| Frontier | `frontend/data/backcast/keepers/PJM.json` → `frontier` | **DECLARED 2026-07-31** at pjm-142, unchanged |
| Lever queue | `docs/mechanism-testing-matrix.md` §5.3 | **EMPTY** — items 3/4/5/6/8/10 and root cause 15b all terminal, rule-28(c) column closed at pjm-151 |

**Holdout consequence, stated plainly:** with `final` empty and the freeze
ACTIVE, **2022 (validation), 2019 and H1-2026 (locked test) are ALL closed to
PJM**. PJM's `complete` marker grants nothing spendable today. 2023–2025 only, in
every mode, with no exception for a probe. This session solved nothing, so
nothing was spent.

---

## §2 — Decision 1 restated: `state_carbon_pricing` (PJM cell `O`, PENDING OWNER since pjm-146)

**Nothing changed and nothing is proposed.** Verified at head: PJM's cell in the
`state_carbon_pricing` row is `O` (`cells: ".KOUKK"` against
`isos: ["ERCOT","CAISO","PJM","MISO","NYISO","NEISO"]`), and
`pjm_rggi_allowance_pricing: bool = False` at `scenarios.py:1207` — still gated,
still default-off.

The state of the evidence, unchanged from pjm-146:

* **Built, solved, registered A/B.** **Zero fitted parameters** — published RGGI
  quarterly-auction clearing-price annual means metric-converted at 1 short ton =
  0.907185 t, membership an exact per-plant EIA-860 state test, emission rates
  the fleet's own. DOF ledger 18 → 19 (measured-external) with `n_residual`
  **unchanged at 6**.
* **All five pre-registered gates PASS** (K1 mc identity 3.7e-13; K2 0.0 MW
  control; K3 membership audit clean incl. Virginia's exit; K4 sign; K5
  liveness).
* **Structure improves.** D-2 clears **all three** `CT_PEAKER` forced-share
  FAILs; C3a-2025 improves. It reproduces RGGI leakage endogenously.
* **The blocker.** Determination goes **CALIBRATED → NOT-YET** on an
  **UNLICENSED** C1 `CC_REGULAR` **−16.06 TWh (2023) / −13.84 TWh (2024)** — no
  C1 magnitude gate was pre-registered for it, in the class carrying ~40 % of ISO
  load. Right **in kind**, too elastic in **magnitude**.

**Cost of arming:** PJM stops being a zero-caveat CALIBRATED ISO.
**Cost of leaving it off:** the model carries **no carbon price at all** in the
four PJM states that had one, so the gas/coal merit order there is knowingly
mis-ordered — a disclosed accuracy gap, not a gate failure.

**Named successor if the owner wants the magnitude fixed first:** the **CC→coal
substitution elasticity**, under its **own** charter, identified from PJM's own
record (rule 25). Explicitly **never** a haircut, offset or scalar tuned onto the
adder (rules 13/21/24).

**This session did not arm it and did not flip the cell.**

---

## §3 — Decision 2 restated: sign-off on the G-20b within-window tight-hour memo (item 5)

The memo is written and committed at
`results/calibration/MEMO-pjm153-g20b-within-window-tight-hour-2026-08-04.md`.
It asks one question and answers none of it:

> the merit-order guard vetoes an outage window when **≥ 90 %** of its hours are
> out of merit (`MERIT_OOM_FRAC = 0.90`). The remaining **≤ 10 %** are, by
> construction, the hours the unit *was* in merit — the tight, high-price hours.
> Today the whole window leaves the availability envelope, so the unit is
> returned to the model as AVAILABLE through those hours too. Should it be?

Verified unchanged at head: `scripts/lib/outage_detect.py:450,452` —
`MERIT_RCC_PCTL = 0.90`, `MERIT_OOM_FRAC = 0.90`. **No guard parameter moved
(rule 23).**

The memo states the evidence **both ways** and recommends **no direction**. The
audit's own verdict is UNCHANGED (D2 population test clean 3/3 for PJM; D3
exceedance mostly a window-**length** effect).

**What is requested is a yes/no on chartering a charter — not a fix.**

* **YES** authorizes a charter bound by memo **§5 and only §5**: an hour-grain
  **REPLACEMENT** of the window-grain veto (rule 19 `[R-ONE-MECH]` — never a
  stack); **zero fitted parameters**; `MERIT_OOM_FRAC` / `MERIT_RCC_PCTL`
  **FROZEN** (rule 23); scored on the **tightest-decile amplitude**, never the
  annual mean (PJM's level passes by cancellation: +$6.82/+$5.78/+$3.40 overnight
  against −$7.62/−$11.37/−$22.19 at peak); a **mandatory C3c report** (model tail
  3/10/32 h); **LOYO within 2023–2025**; and kill rules **K1–K4** as written
  (K1 <1 % reclassified span → dead at the pre-check, no LP; K2 <$1.00/MWh
  tightest-decile → inert; K3 any C1-gated class >1.5 TWh → out of lane; K4
  unlicensed determination move → refused).
* **NO** is a complete and final answer: matrix §5.3 item 5 and keeper root cause
  (6b)'s remnant both close as **owner-refused**, and the pjm-138 §4.2 price
  becomes a disclosed representation cost rather than an open lead.

---

## §4 — What this session deliberately did NOT do

* **Did not arm `state_carbon_pricing`**, with or without a magnitude correction.
  Arming it on a haircut/offset/scalar sized on the C1 residual is barred
  (rules 13/21/24), and arming it as-is spends PJM's zero-caveat status on an
  unlicensed regression.
* **Did not charter the G-20b successor.** Chartering without the owner's yes
  would be a session picking up an owner-gated lever on its own authority.
* **Did not manufacture a successor lever.** The queue is empty by measurement,
  not by oversight; the frontier is owner-declared.
* **Did not re-open any terminal item** (3/4/5/6/8/10, root cause 15b) and did
  not re-test any cell marked `R`/`I`/`G` — no new evidence exists to justify it
  (rule 28(a), DO-NOT-REDO).
* **Did not touch a holdout year in any mode**, not even as a probe. The freeze
  outranks the marker and only the owner lifts it — never a session, and never by
  inference from a passing metric.
* **Did not move a cell verdict.** No mechanism was tested, so rule 28(b)'s
  update duty does not fire. Recording the parked state is documentation, not a
  verdict.

---

## §5 — Known-open objects restated, NOT landed here (each needs its own charter)

* **Cross-ISO thermal-tranche artifact staleness.** PJM's `ST_GAS` `online_frac`
  is **0/10**; CAISO **0/70** across all four groups; NEISO and NYISO have no
  column at all. Regenerating any of them rewrites `committed_pct` /
  `online_frac` / `chp_pmin_cf` for `COAL` / `CC_REGULAR` / `CT_PEAKER` — columns
  **ARMED keeper floors read** in several ISOs. Needs a cross-ISO charter with a
  **CONTROL ARM**, never a side effect of another lane. Related object on the
  MISO side (miso-127 §7): 37–39 % of the model's `ST_GAS` class energy has no
  committed bench counterpart. **Same artifact family — one lane must not land
  the other by accident.**
* **`pjm_reserve_supply_cap`** — adjudicated at pjm-153 as a rule 19
  `[R-ONE-MECH]` **enforcement gap** (three read sites, all unreachable; all 15
  committed PJM bundles pjm136→pjm151 armed-and-unobservable). **Filed, not
  deleted:** the one-line guard that closes it would make the current keeper's own
  recorded config raise, so it is an owner call.
* **Stale `scenarios.py` line anchors in the matrix** — warnings owned by whoever
  next moves `scenarios.py`. Not touched here; this session did not move it.

---

## §6 — Rule compliance

* **Rule 1 `[R-STRUCT]`** — nothing judged by fit; nothing armed to reach a
  number.
* **Rules 13/21/24** — no adder, haircut or scalar proposed or sized on any
  residual; the RGGI magnitude defect is routed to a named successor charter, not
  patched.
* **Rule 15** — no run was produced, so there is nothing to register. The dashboard
  is untouched and correct.
* **Rule 16** — no solve, so the all-years duty does not fire.
* **Rule 19 `[R-ONE-MECH]`** — the G-20b route is restated as a **replacement**,
  never a stack; `pjm_reserve_supply_cap` left filed.
* **Rule 22 `[R-HOLDOUT]`** — no out-of-training year solved, scored, read or
  registered. Freeze ACTIVE and verified enforced before the marker.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no parameter re-derived; guard constants
  verified unmoved at 0.90/0.90.
* **Rule 25 `[R-ISO-SCOPE]`** — no verdict imported into PJM from another ISO; no
  other ISO's cell written by this PJM session.
* **Rule 22 D-5(b)** — no promotion, so no re-key and no determination
  re-verification is owed. `audit_keepers.py --iso PJM` PASSes at head regardless.
* **Rule 27 `[R-PUSH]`** — no source file ≥300 lines rewritten; this session adds
  documentation only.
* **Rule 28(b)** — no mechanism tested, so no cell verdict moves. The §5.3 parked
  block is recorded in the same session.

---

## §7 — The ask

**Two answers unblock this lane. Either one, or both, or an explicit "leave it
parked" — all three are complete answers.**

1. **`state_carbon_pricing`** — arm as-is (accepting the unlicensed C1
   `CC_REGULAR` regression and the loss of zero-caveat CALIBRATED status), leave
   off, or charter the **CC→coal substitution elasticity** successor first.
2. **G-20b hour-grain replacement** — charter it under memo §5 (yes), or close
   item 5 as owner-refused (no).

Until then the honest state is the one recorded here: **PJM is CALIBRATED with
zero FAILs and zero CAVEATs, its lever queue is empty, its frontier is declared,
its holdout years are all frozen, and its two remaining moves both belong to the
owner.**
