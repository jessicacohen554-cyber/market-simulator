# PREREG miso-167 — `miso_reserve_online_gated`: reserve SUPPLY restricted to synchronised capacity

**Pre-registered 2026-08-18, before any construction or solve.** Keeper at pre-registration:
`2026-08-16-miso-160-wefor-shape`. Evidence base:
`FINDING-miso167-summer-scarcity-anatomy-2026-08-18.md`.
**Nothing in this document is armed.** It exists so a successor session with adequate RAM can
execute it without re-deciding anything, and so its predictions are on record before its numbers are.

---

## 1. The defect, stated falsifiably

`model/reserves/spec.py::_miso_design` leaves `ReserveDesign.online_gated = None`, so MISO's
reserve requirement may be backed by the headroom of capacity that is **not synchronised**. In the
47 actual summer-2025 RT>$200 hours the model meets a 5.21 GW requirement while CT_PEAKER carries
8.23 GW of idle (45.2 % of available) capacity, and the reserve dual sits at $10.71 against MISO's
own published ASM MCP of $484.87. *[Corrected 2026-09-01, xiso-cascade: $484.87 sums a nested
cumulative cascade; the published price a reserve MW earns is the cascade top, $193.30. Evidence
context only — every §3/§6 gate below is MW- or criterion-based and none derives from this figure,
so the pre-registration stands as written. `docs/FINDING-xiso-cascade-scan-2026-09-01.md`.]*

**Falsifiable claim:** the model's reserve constraint is dormant in MISO's tight hours *because*
reserve supply is unrestricted, not because MISO's system was comfortable. Restricting supply to
resources that can physically provide each product makes it bind.

## 2. The mechanism

`miso_reserve_online_gated: bool = False` — **GATED, default OFF**, MISO-only.

Splits the market-wide `miso_rbdc` family's single reserve class into two, following the published
MISO BPM-002 product definitions:

- **online-gated class — Regulating + Spinning.** Both products require a resource *synchronised
  to the grid* (Reg additionally on AGC). Backed by the existing ISO-agnostic row form in
  `model/lp/reserve_rows.py`: `R[c,z] − online_rho · Σ_g P[g] ≤ 0`, so offline capacity
  contributes nothing and only online generation backs the product.
- **ungated class — Supplemental (+ Short-Term Reserve).** Explicitly offline-eligible: MISO's
  Supplemental product may be supplied by offline quick-start resources. Left ungated, exactly as
  today.

Per-product requirements come from the **already-committed** measured series behind
`miso_measured_reserve_requirements` (`data/raw/MISO-AS/asm_rt_cleared_mw_<y>.parquet`, region ×
product cleared MW), which the loader already reads per product. Measured summer-2025 mix:
reg 0.738, spin 0.840, supp 1.063, str 0.409 GW.

**Degrees of freedom added: ZERO (rule 21 `[R-DOF]`).**
- The class split is a published product definition, not a parameter.
- The requirements are measured, already in-repo, already loaded.
- `online_rho` is a **fleet property**, derived from MISO's own fleet the way the existing gated
  classes derive theirs ((pmax−pmin)/pmin near min load) — **derived from MISO data, never
  imported from NYISO or PJM** (rule 25 `[R-ISO-SCOPE]`). It enters the matrix as `U`.

**Forward story (rule 13 `[R-MEASURED]`):** the gate regenerates in any forecast year from the
published requirement and the fleet's own online state. It responds to changed conditions — a
fleet with more synchronised capacity binds less. Nothing measured-outcome-shaped enters.

**Rule 19 `[R-ONE-MECH]`:** this is the sole mechanism for reserve-supply eligibility at MISO. It
does not stack on `ordc_scarcity_overlay` (cell `G`, and untouched — that refusal concerns the
reserve DEMAND curve, this is the SUPPLY side) and it must not be armed together with any future
`measured_ramp_capability` qualifier without an explicit reconciliation.

## 3. The no-LP pre-check — RUNS FIRST AND CAN KILL THE LEVER

Executed on the keeper's own committed P1 at **tranche grain** (the class-grain sizing in the
finding is not sufficient: a plant with any tranche dispatching is synchronised, so its remaining
headroom is legitimately online).

Measure, in the 47 summer-2025 RT>$200 hours: **H_on** = reserve-capable headroom on units with
P>0, and **H_off** = capacity on units with P=0.

- **K-PRE-A (inertness kill).** If `H_on ≥ (reg+spin requirement)` in **≥ 80 %** of the 47 hours,
  the gate cannot bind where it matters → **DECLARE INERT, mint cell `I`, DO NOT SOLVE.**
- **K-PRE-B (over-reach kill).** If `H_on < (reg+spin requirement)` in **≥ 99 %** of ALL 8,760
  hours of any year, the gate binds nearly everywhere rather than in tight hours → the
  construction is wrong (likely `online_rho` mis-derived); **fix or abandon, do not solve.**

Both thresholds are fixed here, before measurement.

## 4. Disclosed direction — stated before the solve, and NOT claimed as skill

The arm **RAISES** prices in tight summer hours. This is disclosed, not discovered. In particular
it will raise 2023 and 2024 too, where the model's annual C3a is already slightly high
(2023 +0.6 %). **That is the binding risk of this lever**, and it is why the decision rule below
is asymmetric: closing C3a-2025 while pushing C3a-2023 out of band is a FAIL, not a trade.

Magnitude bound from the finding §5: the reachable (DA-foreseen) half is worth at most ≈ +3.3 pp
on C3a-2025. **A measured move materially larger than that is evidence the mechanism is reaching
hours it should not** — report it, do not celebrate it.

## 5. Solve protocol

- Same-HEAD **zero-delta control** + **arm**, both registered (rule 15 `[R-DASHBOARD]`).
- `--year 2023 2024 2025` in ONE invocation each, years **sequential** (rules 12, 16).
- Control must reproduce the committed keeper bit-identically before the arm is read.
- **[R-HOLDOUT] fail-closed:** MISO holds neither `complete` nor `final`; the spend freeze is
  ACTIVE. **2023–2025 ONLY.** No touchpoint, no locked-test year, under any result.

## 6. Decision rule — fixed before the numbers

**PROMOTE** iff all of:
1. **K-1** No criterion-year PASS→FAIL flip in any of 2023/2024/2025, C3a-2023 and C3a-2024
   included (the against-interest guard of §4).
2. **K-2** C3b NRMSE does not cross its 0.200 gate in any year.
3. **K-3** C8 forced-share passes in both arms; no material class newly over budget without a
   D-4-clearing window.
4. **K-4** C6 attested at promotion.
5. **K-5** The reserve dual moves in the DA-foreseen hours specifically — the hours the mechanism
   claims. A price rise concentrated in RT-only hours means it is reaching hours a deterministic
   LP should not reach; that is a **FAIL**, whatever it does to C3a.

**C3a-2025 closing is NOT a promotion condition** (rule 1 `[R-STRUCT]`). The mechanism is promoted
on structural fidelity — reserve supply restricted to resources that can physically provide the
product — or not at all. If every gate passes and C3a-2025 still fails, the mechanism stays and
the determination stays NOT-YET at full magnitude.

**ESCALATE to the owner** (do not self-promote) if K-1 fails only on C3a-2023 while C3a-2025
improves materially: that is the cancellation trade the finding §1 warns about and it is the
owner's call, not the session's.

## 7. Leave-one-year-out

Per rule 22, a mechanism-change-driven verdict flip is scored leave-one-year-out within 2023–2025
before promotion. In-sample gain with held-out degradation is overfitting, not skill.

## 8. Execution blocker

**Not runnable in the miso-167 container: 15 GB RAM against miso-161's measured >13.9 GB/year for
a MISO plant-level LP.** A successor needs **≥24 GB**. Reported per CLAUDE.md rather than routed to
a CI runner (the GitHub Actions prohibition).
