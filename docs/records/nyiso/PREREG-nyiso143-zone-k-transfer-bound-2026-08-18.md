# PREREG nyiso-143 — the chartered Zone-K reconciliation, written as the transfer bound alone against the CORRECTED control

**Written BEFORE any solve is launched.** Charter:
`docs/DECISION-CARD-nyiso137-zone-k-charter-2026-08-16.md` (D1 **GRANTED**,
2026-08-16: *"Grant — write, prereg, solve"*). Re-scoping:
`results/calibration/FINDING-nyiso139b-zone-k-joint-lever-rescoped-2026-08-16.md`.
Both blocking questions answered by the owner at
`results/calibration/FINDING-nyiso140-li-st-floor-membership-2026-08-16.md` §6.

---

## 1. WHY THE "JOINT" ARM IS A SINGLE-FLAG ARM — the charter's own sequencing decided this

The charter asked for the mainland→Zone-K transfer bound **and** the downstate
ST_GAS `min_gen` floor reconciled as ONE mechanism under rule 19
`[R-ONE-MECH]`. Three owner-level facts have since collapsed that into one
writable object, and none of them is a session judgement:

1. **The floor limb the card paired with the bound was already disabled.**
   `Long_Island:ST_GAS:tmax:LI_ST_ev` — the only ST_GAS limb whose window
   coincides with the bound's own HB14-21 application window — is off on the
   keeper via `NYISO_PEAK_WINDOW_FLOORS_OFF`. Disabling it is a no-op
   (nyiso-139b §2).
2. **The live limb's window was adjudicated CORRECT and its MEMBERSHIP was the
   defect** (owner, nyiso-140 §6.1). The always-on 24-hour base stays; Port
   Jefferson (2517) was removed from it.
3. **The owner ORDERED the two apart** (nyiso-140 §6.2): *"STANDALONE ARM
   FIRST, then Zone-K … the transfer bound and this floor are **not one
   phenomenon**, so folding them into one bundle would confound a rule-17 bug
   fix with an untested lever."* That standalone arm is
   `2026-08-16-nyiso-140-layup-exclusion`, and it is **in the control**.

So the floor side of the reconciliation is **already landed**. What is left to
adjudicate is the transfer bound, against a control that now carries the
corrected floor. **This is NOT the nyiso-130 re-test that rule 28(a) forbids** —
three things differ, each independently sufficient as new evidence:

| | nyiso-130 (verdict `R`) | this arm |
|---|---|---|
| control | pre-repair; Port Jefferson absorbing 72.6 % of the LI limb's forcing | post-repair (nyiso-140) **and** post-benchmark-correction (nyiso-142) |
| kill gate | **K6** — "any D-2 mechanism's forced share rises" | **K6′** — owner-adopted successor (nyiso-140 §5/§6.3) |
| K6′ leg (a) | n/a | non-vacuous for the first time: the D-4 **per-unit conduct rider** ships in this session |

## 2. THE LEVER

`ScenarioConfig.nyiso_li_tsl_n11_security` — `False → True`. It changes the
basis of the NYC→Long_Island HB14-21 import cap from NYISO's published Zone-K
**Locality Import Limit** to the published **N-1-1 Transmission Security
Limit**, 940 MW (`model/interchange/nyiso.py::apply_nyiso_li_tsl_import_cap`).

* **Rule 21 `[R-DOF]` — ZERO new free parameters.** The 940 MW is read from
  TABLE 1 note 2 of NYISO's Locality Bulk Power Transmission Capability
  Reports, identically in the 2024-25, 2025-26 and 2026-27 editions
  (`results/calibration/_nyiso130_li_tsl_identification.json`). The DOF ledger
  gains no entry: this SWAPS one published number for another.
* **Rule 14 `[R-ACCURATE]`** — the incumbent basis nets a 660 MW
  generation loss-of-source that the model **already carries twice elsewhere**;
  removing the double count is the licence, not the tail count.
* **Rule 25 `[R-ISO-SCOPE]`** — NYISO-only field; every other shard stays `.`/`U`.
* **Config delta: exactly one key.** The arm replays the keeper's own
  `meta.json` with `nyiso_li_tsl_n11_security: true` added to the
  `coal_prb_sigmoid_overrides` generic `with_overrides` channel — the same
  channel `nyiso_li_lcr_tsl` already rides. K1 must show 1 differing field.

## 3. KILL GATES — K1-K5 as nyiso-130 wrote them, K6 REPLACED BY K6′

K1 config isolation, K2 feasibility (dump/slack = 0), K3 liveness (in-window
cap 940 MW in the arm vs 275-325 MW in the control), K4 scope (only
`NYC>Long_Island` bounds move), K5 seam (external import within ±2 %) are
carried **unchanged** from `scripts/probes/_nyiso130_ab_gates.py`; all five
PASSED there and a regression on any of them kills the arm.

**K6′ (owner-adopted, nyiso-140 §5).** A rise in a D-2 mechanism's forced share
is **not itself a kill**. It escalates to provenance + shape and fails only on
a miss: **(a)** every binding mechanism still clears D-4 (window **and**, as of
this session, per-unit conduct); **(b)** the class's D-1 `profile_r` /
`cv_ratio` still clear. The energy-normalised
`Δforced = forced_arm − forced_ctrl × (energy_arm / energy_ctrl)` is reported
at full magnitude, **not gated**.

> **PRE-REGISTERED READING OF K6′ LEG (a), declared here BEFORE the solve
> because this session is what makes the ambiguity bite.** Leg (a) says every
> binding mechanism *"**still** binds only inside its driver-justified
> window"*. "Still" is read as **arm-vs-control**: a mechanism that fails D-4
> in **both** arms is a PRE-EXISTING defect and does **not** kill the arm; only
> a mechanism that **newly** fails in the arm does. This matters concretely and
> immediately: the conduct rider shipped this session FAILS on the designated
> keeper itself (plant **2480 Danskammer**, `Capital_Hudson × ST_GAS`, 2023 and
> 2024 — §5 below), so under an ABSOLUTE reading leg (a) would kill every
> NYISO arm ever written until that separate defect is repaired, which is
> plainly not what the owner adopted. **If the owner overturns this reading,
> the arm is un-adjudicable today and the result must be discarded, not
> re-interpreted.**

## 4. EX-ANTE PREDICTIONS — stated before the solve, including against interest

From `results/calibration/_nyiso130_ab_gates.json` (the same lever on the
pre-repair control):

* **The C3c tail collapses.** nyiso-130 measured 2 / 0 / 5 h against a control
  of 3 / 0 / 14. Expect the same direction. Per the charter's **D2 ruling**,
  only the arm-vs-control **delta** may be relied on; absolute C3c band
  membership is CONDITIONAL and, since the nyiso-139 clock repair landed, is
  scored against the corrected actual tail.
* **The downstate ST_GAS forced share RISES again** (nyiso-130: 0.2042→0.2218,
  0.2204→0.2597, 0.1541→0.1699). This is EXPECTED and is exactly what K6′ was
  adopted to stop treating as a kill: relieving an import bound pushes in-zone
  units from in-merit to at-floor by construction (nyiso-139b §5).
* **Reported against interest:** the class-energy denominator also falls, so
  part of that share rise is mechanical. The energy-normalised Δforced is the
  honest number and it is reported whatever it says.
* **C3a is the risk.** 2025 sits at −9.6 % against a ±10 % band on the
  superseded keeper's basis. If the arm pushes 2025 C3a outside the band the
  arm FAILS on a load-bearing criterion, and no K6′ escalation rescues it.

## 5. DECLARED, PRE-EXISTING, NOT INTRODUCED BY THIS ARM

The D-4 per-unit conduct rider fails on the **control** at plant **2480
Danskammer** (`Capital_Hudson × ST_GAS`): 0.0011 TWh over 102 binding hours in
2023 and 0.0001 TWh over 24 in 2024, measured median output **0.000 MW** in
**100 %** of those hours. It is 0.05 % / 0.004 % of the mechanism's forced
energy. It is a **separate rule-17 `[R-FLOOR-WINDOW]` object** with its own
identification, declared here so it cannot later be read as this arm's doing,
and it is NOT repaired in this bundle (rule 19: one mechanism per arm).

## 6. WHAT PROMOTION WOULD REQUIRE

K1-K5 silent, K6′ clean under the §3 reading, and C1 / C2 / C3a / C3b / C4 /
C6 / C8 no worse than the control — "whatever C3c does" (charter D2, nyiso-130
§8). Both arms are registered on the dashboard whatever the verdict (rule 15),
across 2023 / 2024 / 2025 in one bundle (rule 16), years sequential (rule 12).
