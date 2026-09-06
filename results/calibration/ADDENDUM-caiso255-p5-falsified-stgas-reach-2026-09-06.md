# ADDENDUM to PRECOMMIT-caiso255 — **P-5 IS FALSIFIED.** caiso-254 §3's inertness proof covers 76 % of CAISO's ST_GAS fleet, not "the whole class", and my own PRECOMMIT §1 repeated the error. The repair reaches 918.3 MW of real steamers. **The arm is unchanged; what it may CLAIM is.**

**Session caiso-255, 2026-09-06.** Pushed **BEFORE the screen solve**, because
it corrects a claim two merged documents make. Keeper
`2026-09-05-caiso-252-b1-notrim` UNCHANGED, DETERMINATION **CALIBRATED**.
**ZERO LP spent.**

---

## §C.1 — THE PREDICTION, AND HOW IT FAILED

PRECOMMIT §4 **P-5**: *"phase 0 measures a **strictly CT-side** footprint:
F(y) > 0 in all three years, and **zero** ST_GAS tranches move"*, with the
registered uncomfortable reading: *"the ST_GAS inertness proof (caiso-254 §3)
is wrong, or the artifact edit is reaching rows it does not claim."*

**The first horn is the one that fired.** Per-class footprint, screen year 2023:

| class | tranches | **moved** | F share |
|---|--:|--:|--:|
| CC_REGULAR | 266 | **0** | 0.0 |
| CC_CHP | 129 | **0** | 0.0 |
| CT_PEAKER | 828 | 784 | 11,801.4 |
| CT_CHP | 195 | 147 | 935.2 |
| **ST_GAS** | **25** | **14** | **1,829.7** |
| OTHER (non-gas) | 219 | **0** | 0.0 |

**14 of 25 ST_GAS tranches move, carrying 12.9 % of F(2023).**

---

## §C.2 — WHY: the bypass set is not the class

Every ST_GAS tranche in the 2023 LP fleet, with its Δmc:

| plant | tranches | MW | in `ST_GAS_PEAKER_PLANTS` | max Δmc |
|---|--:|--:|:--:|--:|
| **315** AES Alamitos | 3 | 1,142.0 | **YES** | **0.0000** |
| **335** AES Huntington Beach | 3 | 225.8 | **YES** | **0.0000** |
| **350** Ormond Beach | 3 | 1,491.0 | **YES** | **0.0000** |
| **356** (LA_BASIN) | 8 | **830.1** | **NO** | **$4.4475** |
| **10446** (ZP26) | 8 | **88.2** | **NO** | **$2.3564** |

**The bypass works exactly as caiso-254 proved** — all nine tranches of
315/335/350 move by **exactly 0.0000**. What is wrong is the *set's* claimed
extent. caiso-254 §3 states: *"CAISO's entire ST_GAS fleet is that set: plants
315, 335, 350 … 2,858.8 MW, which is the whole class in
`bin_assignments_CAISO.csv`."*

**The parenthetical is the error, and it is load-bearing.** It is true of
`bin_assignments_CAISO.csv` — that file has **exactly 3 ST_GAS rows**, read and
confirmed this session. It is **not** true of the LP fleet, which builds ST_GAS
from the CAMPD per-plant binning and carries **five** plants:

> **CAISO ST_GAS in the LP = 3,777.1 MW, of which 2,858.8 MW (75.7 %) is
> bypassed and 918.3 MW (24.3 %) is NOT.**

Those 918.3 MW read `offer_curve_by_group["ST_GAS"]`, which
`_ungrounded_source` maps to `CT_PEAKER` — so they are repriced by the CT
bucket's de-contamination, which is exactly what the footprint measured.

**My own PRECOMMIT §1 repeated the error** — *"no ST_GAS band, present or
absent, reaches a CAISO plant"* — and is **WITHDRAWN**. I inherited the claim
without re-deriving its extent from the LP fleet, which is the check that would
have caught it and which P-5 was written to force. P-5 did its job.

---

## §C.3 — WHAT THIS CHANGES, AND WHAT IT DOES NOT

**It does not change the arm.** No config, artifact, gate or threshold moves.
The mechanism is identical; only the description of its reach was wrong.

**It STRENGTHENS the case for option 1 rather than weakening it** — and I note
that this cuts in my favour, so it is stated with the caution that deserves:

* the separated ST_GAS bucket **FAILS G4** with `peak` 1.196 inverted **0.350
  below** `econ_high` 1.546. Under the full three-way adoption those bands
  would have been consumed — and, contrary to §3, they would have reached
  **918.3 MW of real steamers**, handing p356 and p10446 an **inverted offer
  curve** whose top-of-stack capacity is priced *cheaper* than its middle;
* option 1 refuses exactly that, and those two plants instead read the
  **de-contaminated** CT bucket — a curve that passes G4 on its own row;
* so the omission is **not cosmetic**, as PRECOMMIT §1 argued. It is the leg
  that keeps an inverted curve out of the LP.

**A THIRD, INDEPENDENT REASON THE ST_GAS BUCKET WAS NOT READY TO CONSUME —
found by this correction, not previously known.** The derive's G1 for ST_GAS
reconciles a 2,559 MW bid bucket against `fleet_mw` **2,858.8 MW** — the
three-plant `bin_assignments_CAISO.csv` figure. The LP's ST_GAS class is
**3,777.1 MW**. So the ratio 0.895 that PASSED G1 is measured against a fleet
definition **omitting 24 % of the class the bands would price**. That is a
genuine defect in the ST_GAS geometry, it is orthogonal to the G4 inversion,
and it would have gone unnoticed had the bucket been consumed. **It is
queued, not fixed here** — fixing it is a new object needing its own
pre-registration, and this session has an owner-granted scope.

---

## §C.4 — CONSEQUENCE FOR THE SCREEN GATE (registered, not re-specified)

PRECOMMIT §7.2 wrote S-1 as *"CT_PEAKER energy RISES … (the ST_GAS leg is
reported INERT-BY-CONSTRUCTION, not relaxed — caiso-254 §3)"*. The
parenthetical rests on the claim just withdrawn, so it is corrected: **ST_GAS
energy is NOT inert and is expected to move** — p356 / p10446 now read cheaper
CT bands, so their energy should **RISE** alongside CT_PEAKER's.

**The gate itself is NOT re-specified.** S-1 is scored exactly as registered —
on the **CT_PEAKER** leg — and ST_GAS's movement is **REPORTED, not gated**.
Re-writing a gate after seeing a measurement is what stop rule 3 forbids, and
tightening it here would be no more legitimate than loosening it. S-2, S-3,
S-4, the C3a exclusion and the promotion basis §5(8) are all untouched.

---

## §C.5 — DISCLOSURE HYGIENE

This correction was produced by a prediction I wrote to bind and then
falsified, on evidence I generated myself and could have omitted: the phase-0
JSON reports only gas vs **non-gas** movement, and by that field alone the
footprint reads clean (0 non-gas in all three years). **P-5's per-class claim
required a measurement the estimator does not emit**, and scoring it honestly
meant writing that extra probe rather than declaring P-5 satisfied by the
non-gas zero. Evidence:
`_caiso255_p5_perclass.json`, `_caiso255_p5_stgas_diag.json`.
