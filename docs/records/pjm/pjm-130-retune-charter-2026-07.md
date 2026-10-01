# CHARTER — pjm-130, the PJM re-tune opened by pjm-129's NOT-YET

**Lane:** `docs/handoffs/pjm-frontier-path-2026-07.md`; trigger
`results/calibration/FINDING-pjm129-keeper-reaudit-meritguard-2026-07.md` §7.
**Predecessor:** pjm-129 (PR #2972, `cc6b87c`) — the keeper does not hold on the
guard-corrected CAMPD envelope: `CALIBRATED` 10/10 → **`NOT-YET` 7/10** on three
gates, under a measured −1.3 pp structural price reduction that the extract owns
100 % of (code drift measured PJM-inert at $0.000).

## 0. What this session is allowed to do

Settled going in, and **not re-litigated**: the corrected CAMPD envelope stays in
(rule 1 `[R-STRUCT]` + rule 14 `[R-ACCURATE]`); post-keeper code drift is
PJM-inert; the RAM block is a staged one-year-per-process `--reuse-solved` chain,
not a bigger box; both reserve-scoping framings are closed (pjm-124 INERT /
pjm-125 PARTIAL); Lane 2's commitment-status half is closed terminal (pjm-128);
the holdout freeze is active (2023–2025 only, rule 22 `[R-HOLDOUT]`); the keeper
designation `2026-07-25-pjm-121-cc-belt` is unchanged and only the owner moves it.

The three gates, cheapest first (pjm-129 §7):

1. **C1-2023 CC_REGULAR** — −8.10 TWh against an 8.00 TWh band. 0.10 TWh, 1.2 %
   of band, on a class the guard moved by only −0.23 TWh; the row was already at
   98 % of band pre-guard.
2. **C3a-2025** — −10.6 %, needs +0.6 pp. The pjm-120/122/123 dispersion/level
   stratum.
3. **C3c tail 2024/2025** — 0.39× / 0.47×, need ≥0.50×. Downstream of the open
   G-20b/G-22 reserve-tightness root cause.

## 1. Pre-registration discipline, stated honestly

Every measurement in this session was made by a probe whose question, method and
decision rule were **written into its docstring and committed before it was
run** (`0aa1b88`, `b93c305`). **No LP was solved**, so the
"commit the charter before the solve" requirement is satisfied vacuously rather
than by this document — this charter is written after the no-LP probes and says
so. It pre-registers the *solve* decision, and the honest content of that
decision is §3: **no admissible A/B arm exists for this session to run.**

## 2. Gate 1 — pre-registered rule and outcome

Probe: `scripts/probes/pjm130_c1_ccregular_displacement.py`. Question: is the
marginal −0.23 TWh CC_REGULAR's own miss, or displacement by the guard's
returned supply (ST_GAS + COAL + CC_CHP + CT_CHP)?

Pre-registered on 2023:

| test | rule | measured | verdict |
|---|---|---|---|
| M3 displacement | DISPLACEMENT iff ≥60 % of CC_REGULAR's gross hourly loss falls in returned-up hours **and** r ≤ −0.30 | **99.6 %**, r = **−0.369** | **DISPLACEMENT-CONFIRMED** |
| M4 misallocation (the kill criterion) | a structural lever exists ONLY IF some returned class overshoots its *metered* actual while CC_REGULAR is short — otherwise gate 1 has no admissible lever and the session says so rather than pushing 0.10 TWh back | CC_CHP **+2.54 TWh**, ST_GAS **+1.72 TWh** over meter | **lever exists** |

The kill criterion was live: had no returned class overshot its meter, gate 1
would have been ledgered as unclosable-by-structure and nothing built.

## 3. Named exposure, and why no solve is run

**Gate 2 is blocked on an owner decision.** Its only *level*-bearing admissible
route is the measured re-ownership of the $40–150 region (pjm-122), and the
measured surface that carries it is inadmissible until
`docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md` is decided (rule 23
`[R-FROZEN-DERIVE]`). **Checked this session: still undecided** — the memo's last
commit is `f1070d4` and no decision has landed. Not nudged, not re-derived, not
worked around.

**Gate 3 needs a root cause this lane cannot reach.** Both scoping framings are
closed and pjm-125 measured the shared floor at 5.0–5.6× the requirement, of
which 17.5 GW is Non-Synchronized Primary reserve untouchable by *any* commitment
mechanism — so a MIP would not close it either. Ledgered, not mechanised
(rules 1 / 19 `[R-ONE-MECH]`).

**Gate 1's lever is not yet armable** — see §4.

Building an arm for any of the three under these conditions would mean fitting a
mechanism to a residual, which rules 1 `[R-STRUCT]`, 23 `[R-FROZEN-DERIVE]` and
26 `[R-DELETE]` forbid. **A no-solve session is the correct outcome**, and it is
the established PJM pattern: pjm-124/125/126/127/128 each closed or advanced a
lane on a no-LP pre-check with no solve spent.

## 4. What this session did instead — the prerequisite it found

Gate 1's largest structural signal is **CC_CHP overshooting its metered actual by
+2.54 TWh in 2023** — measured against a `classFull` bench cell that the scored
run **writes itself** from its own `btm.parquet`. pjm-129 flagged the symptom (a
*negative* metered volume, `classFull.CT_CHP = −0.3726 TWh` in the committed
2025 bench) and was forbidden from touching it. Tuning a class against a number
the run authored is not admissible, so the artifact is a **prerequisite for gate
1, not a side item**.

Probe `scripts/probes/pjm130_chp_bench_attribution.py` localized it and the
defect is fixed (`03e105f`): `--btm-backfill-year` repaired the subtrahction's
**subtrahend only**. Detail and measurements:
`results/calibration/FINDING-pjm130-gate1-and-bench-symmetry-2026-07.md`.

## 5. Kill criteria pre-registered for the NEXT session's solve

Whoever arms gate 1 inherits these, unmet-means-dead:

- The arm must **reduce the CC_CHP and ST_GAS overshoot against the meter**, not
  merely raise CC_REGULAR: a lift that moves CC_REGULAR while leaving the
  returned classes above their metered energy is displacement-neutral and is the
  refutation signature.
- **C1 must not lose a free class** (A1 is 15/16, free 11/12).
- The 2023 fuel-family gate (C2) must stay PASS.
- Scored **leave-one-year-out within 2023–2025** before any promotion flag
  (rule 21 `[R-DOF]` / rule 22).
- Rule 16 `[R-ALLYEARS]`: 2023 + 2024 + 2025 in ONE bundle; any single-year solve
  is a throwaway diagnostic and is deleted, never registered.

## 6. Rule compliance

* **Rule 22 `[R-HOLDOUT]`:** no year outside 2023–2025 touched; the freeze is
  untouched and NOT lifted.
* **Rule 15 `[R-DASHBOARD]`:** no solve completed, so there is no bundle to
  register. Nothing was solved and silently dropped.
* **Rules 20 / 23 / 24:** nothing tuned. No offer-curve band, sigmoid, floor,
  ORDC parameter or surface JSON touched; no measured-behaviour constant
  re-derived.
* **Rule 27 `[R-PUSH]`:** the one core file edited (`run_calibration_full.py`,
  10,422 lines) was edited in place and blob-verified against the remote after
  push.
