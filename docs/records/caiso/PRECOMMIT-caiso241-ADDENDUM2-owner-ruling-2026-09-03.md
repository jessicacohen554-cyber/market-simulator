# PRECOMMIT ADDENDUM 2 — caiso-241: the owner's two rulings, and the run design they change

**Pushed BEFORE any LP runs.** The ruling, mechanism, envelope, predictions and
gates are fixed in `PRECOMMIT-caiso241-ct-peaker-committed-2026-09-03.md`
(`cf05a372`) and `PRECOMMIT-caiso241-ADDENDUM-arm-2026-09-03.md` (`81b1aa80`),
both on `origin` before any fleet was rebuilt or any bound evaluated. This file
records the owner's answers to the two asks those files put, and the **changes
to the run design** they require. Nothing else is revised: the §1 ruling, the
§2 mechanism, the §3/§A5 envelope, the §4 predictions and the §5.9 promotion
rule all stand exactly as pre-registered.

**ZERO SOLVES so far.**

---

## §B1 — OWNER RULING 1: **THE SOLVE IS FUNDED**

Ask 1 (precommit §6) — the CAISO lane is at terminal rest (caiso-201/222 Q1) and
caiso-240's CT_PEAKER measurement is the funding case. **Owner: fund it — solve,
register, and promote if the gates pass.**

The pre-registered promotion rule (§5.9) is unchanged and is the one that
applies: promote iff G-STRUCT, G-INERT, G-C1, G-C3b, G-C8, G-CAVEAT and G-C6
pass **and** G-C3a's **verdict** leg passes; the basis is **structural** and a
C3a improvement is **reported and excluded from the basis** (rule 1
`[R-STRUCT]`, precommit §0.7). The owner's standing standard — *"if structural
integrity improves but gates regress that may still be a keeper"* — applies as
written.

Funded knowing what §A6 already settled: the arm can close **at most
16 % / 6 % / 6 %** of the CT_PEAKER volume gap and **cannot flip C3a in any
year** even at its measured maximum.

---

## §B2 — OWNER RULING 2: **THE caiso-231 "NO CONTROL ARMS" DIRECTIVE IS AMENDED**

Ask 2 (precommit §6, from caiso-239 §6.1) — this arm is expected live in all
three years, so caiso-240's dispatch-identity form of G-CTRL has no inert year
to bind on, and the caiso-231 directive left it with no dispatch-level check at
all. **Owner: carve out a control arm for arms live in every year.**

**THE AMENDMENT, AS IT WILL BE CITED.** The caiso-231 standing directive
(*"that's one in like 1000 runs … I don't want to measure drift"*) stands as the
default: a single-delta calibration arm is solved once and scored against the
committed keeper. **CARVE-OUT: an arm measured LIVE IN EVERY SOLVED YEAR — so
that neither the `run_config` field-diff form nor the caiso-240
dispatch-identity form of G-CTRL can bind — MAY spend ONE control solve
(flag-off at HEAD), and its mechanism effect is then measured against that
control rather than against the committed keeper.** The condition is the whole
of the carve-out: an arm with even one inert year takes the caiso-240
dispatch-identity leg and spends nothing. Cost, accepted by the owner: it
doubles the LP cost of such a run and of every future arm in the same position.

*(Genealogy: raised caiso-239 §6.1, escaped by caiso-240 §6.3 because that arm
had an inert year, met for the first time here, ruled 2026-09-03.)*

---

## §B3 — THE RUN DESIGN, REVISED BY §B2

**TWO invocations**, each `--replay-bundle` on
`results/calibration/caiso240_b1_stgas_peak_measured`, each **2023 / 2024 / 2025
sequential in ONE invocation and ONE bundle** (rules 12 `[R-PARALLEL]` /
16 `[R-ALLYEARS]`), differing in **exactly one flag**:

| | bundle | delta |
|---|---|---|
| **A0 — control** | `caiso241_a0_control` | none — the keeper's own recipe, replayed at HEAD |
| **B1 — armed** | `caiso241_b1_ctpeaker_committed` | `--caiso-ct-peaker-committed-measured` |

Launched as concurrent background invocations, capped at the **2** rule 12
allows for a per-plant multi-zone LP; years stay strictly sequential **within**
each invocation.

**Both bundles are registered on the dashboard in this session** (rule 15
`[R-DASHBOARD]` — every completed run, keeper or probe). A0 is registered as a
control probe and is **never** a promotion candidate.

---

## §B4 — G-CTRL, RE-SPECIFIED FOR THE THIRD TIME, AND ITS FALSIFIER

The gate's history, so no future session re-discovers any of it:
1. **"one `run_config` field differs"** — UNSATISFIABLE against a keeper more
   than a day old (caiso-239 measured 22 differing fields, all HEAD drift).
2. **dispatch-identity in a measured-inert year** (caiso-240's re-spec) — needs
   an inert year; **this arm has none**, which is what produced ask 2.
3. **NOW, under §B2: a HEAD-DRIFT check against a real control.**

**G-CTRL (form 3).** **PASS** iff **every scored criterion's verdict in A0
matches the committed keeper's** (`caiso240_b1_stgas_peak_measured/metrics.json`).
The drift's magnitude is reported at full size whatever it is — no tolerance is
declared for the numbers, because the keeper's `git_sha` (`6671c650`) is days
and ~40-commits-a-day behind HEAD and a tolerance chosen now would be a fitted
number. **FALSIFIER:** any scored-criterion verdict differs between A0 and the
keeper ⇒ HEAD drift is material, the keeper-relative comparison is unsafe, and
this is reported as a blocking finding rather than absorbed into the arm's
result.

**CONSEQUENCE FOR EVERY OTHER GATE, AND IT IS THE POINT OF THE AMENDMENT: the
mechanism's effect is measured as B1 − A0, never B1 − keeper.** G-INERT, G-C1,
G-C3a (both legs), G-C3b, G-C8 and G-CAVEAT are all evaluated on that
difference. In particular the §A5 envelope
(`[−0.8798, +0.05] / [−0.3804, +0.05] / [−0.1979, +0.05]` $/MWh) is a bound on
**B1 − A0**, which is what it was always an estimate of — the control makes the
comparison honest rather than merely closer. The keeper-relative numbers are
reported alongside, as the drift decomposition.

**P-8 becomes directly checkable** rather than inferred: it predicted no inert
year exists, and B1 − A0 measures that per year.

---

## §B5 — UNCHANGED

The §1 admissibility ruling and its five limbs; the §2 mechanism (`committed :=
phys_committed`, zero free parameters); the §3/§A5 two-sided crossing envelope
and its two falsifiers, never re-fitted; all eight §4 predictions exactly as
registered (P-3 and P-5 already confirmed pre-solve in §A2); the §5.9 promotion
rule and its exclusion of C3a from the basis; the §0.3 hard stops (training
window only, no `calibration-complete.json` / `holdout-freeze.json` / other
ISO's files, no P2, no off-registry knob, no derive re-run); and the §0.4
DO-NOT-REDO list — in particular that the measured **BID** committed multiplier
(CT bucket 1.166) stays **unarmed** for every CAISO gas class.
