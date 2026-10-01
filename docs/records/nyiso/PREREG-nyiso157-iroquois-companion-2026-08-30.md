# PREREG nyiso-157 — the iroquois winter-spread COMPANION re-test, on the seam arm that lets the cutset bind

**Filed BEFORE the companion solve.** The seam A/B of this session is complete
and registered (`2026-08-30-nyiso-157-par-control` / `-par-attribution`,
gates `_nyiso157_par_ab_gates.json`); no companion LP has run when this file
is pushed and blob-verified (the intake spec §1 condition 3 ordering).

## §1 — the re-open, on its recorded condition

`nyiso_iroquois_winter_spread` is `R` (nyiso-150, run
`2026-08-22-nyiso-150-winter-spread`): armed ALONE, the LP priced the four
mainland zones as one coupled block — an $8–13/MMBtu measured zonal gas
spread produced ≤$1.1 of price spread, the whole state rose together, and the
premium leaked upstate (W-K3a 0–4 % recovery vs ≥30 %). Its recorded re-open
condition: *"a locational mechanism that lets the west→east cutset bind (the
downstate-premium object of nyiso-122 BLOCKER-A/B); re-test this flag as its
companion, never alone."*

**The condition is met, and the evidence is this session's own A/B:**

* The seam arm passes every standing pre-registered kill gate (K1–K9, two
  scorer-instrument artifacts corrected and documented in
  `_nyiso157_par_ab_gates.json`: the K1 dual-channel echo of the single flag,
  and a K5 conservation leg of this session's own operationalization that
  penalized the arm for landing CLOSER to the measured annual net than the
  control — the prereg-text K5, monthly inside the band, passes).
* The west→east cutset (Upstate_West→Capital_Hudson) now **binds**: Jan+Feb
  spread-hours (> $0.50/MWh) 34 → **435** in 2025 (12.8×), 111 → 1,391 in
  2023, 70 → 262 in 2024; the Jan+Feb NYC−UW gradient moves 0.24 → 4.60
  $/MWh (2025) against a measured Jan-2025 gradient of $14.83. The
  nyiso-150 coupled-block finding no longer describes the armed model.
* **Reported against the strict letter:** the EXECNOTE §5 conjunction reads
  `cutset_binds_2025: False` — its control-leg required < 6 control binding
  hours and the control has 34 (2.4 % of the window). That leg mis-modeled
  "effectively none"; the recorded nyiso-150 condition is about what the
  MECHANISM enables, and a 12.8× increase to 30.7 % of winter hours is the
  cutset binding. Both readings are on the record; the DO-NOT-REDO bar
  (new evidence) is met either way, since the coupled-block premise of the
  R verdict is measurably gone.

## §2 — the arms

* **Control := the seam arm** `nyiso157_pararm_B`
  (`2026-08-30-nyiso-157-par-attribution`), already solved and registered at
  this HEAD.
* **Arm C := the keeper recipe + BOTH flags** — bundle `nyiso157_iroq_C`:

```
python3 scripts/replay_keeper.py results/calibration/nyiso155_hydro_repair \
  --out-dir results/calibration/nyiso157_iroq_C \
  --set nyiso_seam_par_attribution=true \
  --set nyiso_iroquois_winter_spread=true \
  --note "nyiso-157 companion arm: seam attribution + iroquois winter spread (nyiso-150 re-open condition; PREREG-nyiso157-iroquois-companion-2026-08-30)"
```

Single delta vs the control: `nyiso_iroquois_winter_spread` False→True
(expected through both recording channels, as documented for K1). Years
2023 2024 2025, one invocation, freeze ACTIVE, no other year.

## §3 — gates: nyiso-150 §4 VERBATIM, re-scored against the new control

W-K1 through W-K6, ADV-W1 and ADV-W2 of
`PREREG-nyiso150-gradient-winter-and-reserve-rearm-2026-08-22.md` §4 apply
**as written**, with exactly one re-basing: every "control" reads the seam
arm (`nyiso157_pararm_B`), because the companion condition itself is the
mechanism difference between the two tests. Specifically:

* **W-K1** exactness — sole differing field `nyiso_iroquois_winter_spread`
  (dual-channel echo counted as the one flag).
* **W-K2** construction + liveness — (a) NYC monthly gas identical on/off;
  (b) annual conservation ≤ $0.005/MMBtu; (c) DJF mean |ΔLMP| > $1/MWh.
* **W-K3** target, gated months Feb-2023 / Dec-2024 / Feb-2025: (a) ≥30 %
  spread-gap recovery per downstate zone, +15 % overshoot kill (Jan-2025
  reported, not gated); (b) annual eqh gradient at least doubles toward
  actual in 2024 and 2025, ≤ actual × 1.10; (c) UW-2023 annual over-pricing
  strictly improves vs the new control; (d) anti-relocation — worst-zone
  |annual eqh error| not past the control's, per year.
* **W-K4** conduct — zero NEW failing D-rows vs the new control; C8 PASS.
* **W-K5** criteria — C1/C2/C3a/C3b/C4/C8: no PASS→FAIL vs the new control
  in any year. **The control's own C3b-2025 stands FAIL (0.203)** — so W-K5's
  C3b leg reads "no NEW failure": FAIL→FAIL is not a flip; a 2023/2024
  C3b flip is. C3c reported at full magnitude, never gated here (ledgered
  limitation; nyiso-137 clock caveat — deltas only).
* **W-K6** LOYO — gate-side: W-K3(a) per gated month separately, W-K3(b) in
  2024 and 2025 separately. Derive-side vacuous (zero fitted parameters).

## §4 — predictions, falsifiable, registered before the solve

* **PC-1.** With the cutset binding, the measured winter gas spread now has a
  transmission constraint to price against: the gated-month downstate−UW
  spread recovery clears the ≥30 % bar that read 0–4 % on the coupled block.
* **PC-2.** UW does NOT rise with downstate in the gated months (the leak
  path is broken); UW-2023's over-pricing improves (W-K3c direction).
* **PC-3.** C3a-2025 is NOT predicted to close: the winter face is at most
  partially this chain's (the summer face is the ledgered C3c object), and
  the seam arm alone moved 2025 lw DOWN (−10.8 → −12.0 %). The companion
  raises downstate winter prices, so the 2025 lw moves back up by some
  amount; landing in band would be a surprise to investigate, not bank.
* **PC-4 (adverse, named).** Dec-2025 may over-raise (nyiso-82 measured
  −3.0 → +7.5 % on the old keeper); bounded by W-K3(d), reported in full.

## §5 — DOF, blast radius, decision rule

* **Zero new free parameters.** The iroquois construction is the resolved
  reconciliation of three measured series (SOM annual + AGT scarcity shape +
  Algonquin ceiling; scenarios.py:5004); the seam arm's ledger is unchanged;
  `n_residual` stays 6. Any value outside the standing tables stops the lane.
* **Untouched:** every scarcity/ORDC/floor/reserve mechanism; the hydro
  input pair; TTC statics beyond what the seam arm already replaces.
* **Decision rule:** any W-gate fires ⇒ the companion registers as a
  rejected probe and the R cell re-stamps with the companion-test outcome —
  the seam arm remains this session's candidate. All gates silent + live ⇒
  the companion PAIR (seam + iroquois) is the candidate on rule 1/14
  grounds. Either way exactly ONE promotion happens this session, of the
  surviving candidate, under the owner's 2026-08-30 in-session ruling
  ("If structural integrity improves but gates regress that may still be a
  keeper"), with the determination re-verified explicitly and every
  regression reported at full magnitude (D-5(b) honored by that ruling,
  never silently). Rule 15: the companion registers whatever the outcome.
