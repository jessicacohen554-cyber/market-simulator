# PREREG — nyiso-110: flag-only `nyiso_spin_reserve_online` single-delta arm (the peak-half reserve-formation probe)

**Date:** 2026-08-02, committed and pushed BEFORE either arm is solved.
**Diagnosis this is built on:**
`FINDING-nyiso110-peak-half-decomposition-2026-08-02.md` (§2 the measured
formation gap, §5-E4 the liveness census, §6.1 the route adjudication).
**Keeper under test:** `2026-08-01-nyiso109-zonal-margin-anchor`
(`results/calibration/nyiso109_zonalanchor_B`), CALIBRATED-WITH-CAVEATS, C3c
the sole ledgered caveat.

## 1. The lever, and why it is off-queue

Single delta: **`nyiso_spin_reserve_online = true`** — the existing,
default-off nyiso-84 mechanism that re-classes the published NYCA 10-minute
SPINNING family (655 MW, $775 RCPF ceiling) onto the online-gated class-2
reserve machinery, so idle quick-start capacity stops satisfying a
requirement whose product definition is synchronized supply. **No code
change, no new ScenarioConfig field, no new derive, zero new DOF.** (The
East spin family shares the gate in code but is not built on this keeper —
`nyiso_east_reserve_families=false` — so exactly one family re-classes.)

Off-queue justification (rule 28a): §5.5 carries no admissible peak-half
lever, and the nyiso-110 decomposition measured the peak-half miss to be
dominated by everyday reserve-price formation the keeper's co-opt never
produces (dual > $0 in 17/6/34 hours vs a measured DA spin price > $1 in
100 % of peak-window hours; passthrough slope ≈ 1). Re-testing a
family-note-adjudicated flag is licensed by new evidence on both of
nyiso-84's grounds: the TARGET is new (everyday formation, never scored
there — its C3c verdict is not contested and is not re-tested), and the
SUPPLY STATE is new (nyiso-84 ran at the pre-hydro-repair HEAD; on the
repaired keeper, hydro's zero-cost headroom covers the requirement in
82–89 % of all hours but only 36–51 % of peak-window hours — E4 — so the
gate's bite is now peak-concentrated and the recorded overnight
GT-forcing objection no longer reaches the hours it fired in).

## 2. Rule-17 shape

* **Driver:** ASM §2 product definition — spinning reserve is supplied by
  synchronized resources; an idle peaker cannot be spinning. Requirement:
  the published 655 MW NYCA spin cell, static in the measured as-enforced
  series in all three training years.
* **Window:** all hours (the published requirement is all-hours). Where it
  may BIND, and why: hours where zero-opportunity-cost synchronized headroom
  (hydro + online gated output) falls short of 655 MW — measured
  peak-concentrated on the keeper's own hourlies (hydro-short in 49/64/61 %
  of peak-window hours vs 11/18/12 % of all hours; E4).
* **Forward story:** regenerates from the published requirement + the
  fleet's online state; the ρ multiplier is the gated fleet's own
  (pmax−pmin)/pmin property clipped to [0.5, 4.0]. No fitted scalar.

## 3. The runs

Same-HEAD zero-delta control + single-delta arm, each ONE invocation over
the FULL span (rule 16), sequential (one per-plant LP at a time):

```
python scripts/replay_keeper.py results/calibration/nyiso109_zonalanchor_B \
    --out-dir results/calibration/nyiso110_control_A \
    --note "nyiso-110 same-HEAD zero-delta control (PREREG-nyiso110)"
python scripts/replay_keeper.py results/calibration/nyiso109_zonalanchor_B \
    --set nyiso_spin_reserve_online=true \
    --out-dir results/calibration/nyiso110_spinonline_B \
    --note "nyiso-110 flag-only spin-online arm (PREREG-nyiso110)"
```

Registration duty (rule 15): BOTH arms register on the backcast dashboard
whatever the verdict, full post-step chain (rebuild-benchmark →
legitimacy_diagnostics → dashboard_add_run → calibration_verdict →
build_status only if the keeper changes), and the matrix cell + §5.5 update
in the registering session (rule 28b).

## 4. Construction gates (all must hold before any score is read)

* **K1 flag fidelity:** the arm's `run_config.json` records
  `nyiso_spin_reserve_online: true`; the control's records `false`; no other
  scenario field differs (K4's diff is the instrument).
* **K2 control integrity, STRICT BYTE basis:** control minus the committed
  `nyiso109_zonalanchor_B` = 0.0 MW on every class-hour of all three years.
  Solve-path commits have landed on main since that keeper's HEAD; their
  NYISO-inertness is a falsifiable expectation, and a non-zero diff halts
  the A/B (no score is read).
* **K3 liveness (the nyiso-87/miso-113 silent-no-op guard):** the arm's
  reserve dual is > $0 in **≥ 500 hours** in every year (nyiso-84's
  gate-only arm produced 652/800/1589 at the truncated-hydro HEAD; E4's
  hydro-short census bounds the binding opportunity at 936/1586/1093
  hours). Below 500 in any year ⇒ the verdict is **INERT (`I`)** — recorded,
  registered, not promoted, and the nyiso-84 class-widening build inherits
  the lane with this arm as its control evidence.
* **K5 full span:** `[2023, 2024, 2025]`, one invocation per arm.
* **K6 direction integrity:** the gate only adds constraints, so no zone's
  lambda may FALL below the control in any hour by more than $0.01; a larger
  fall anywhere is a construction bug — halt, no score.

## 5. Kill gates (any one fires ⇒ CANDIDATE-REJECTED, registered, keeper unchanged)

* **P1 — the pre-registered un-cancellation breach:** C3a-2023 (rt_lw)
  > **+10.0 %** (keeper +7.51; the decomposition predicts upward pressure —
  full measured-content formation would land ≈ +15.1 %, and ~1/3-of-content
  formation sits at the band edge). This kill firing is itself a finding:
  the structurally-correct mechanism colliding with a level gate that
  passes today by cancellation, recorded for the owner's open
  amplitude-criterion call.
* **P2 — band exit anywhere else:** C3a-2024 or C3a-2025 outside ±10 %
  (keeper −0.55 / −9.64; the construction can only raise prices, so 2025
  moves toward band-center by K6 — an exit would mean overshoot past +10).
* **P3 — C1 regression:** any currently-passing class-energy cell flips
  FAIL (keeper: 14/14 all-class, 10/10 free-class, preserved in both arms).
* **P4 — shape regression / the nyiso-84 signature guard:** any
  currently-passing C7/D-1 (year, class) cell flips FAIL; **or** the
  combined CT_PEAKER + CT_CHP overnight (h01–h05) energy rises > 10 % in
  any year — the "forces GT commitment reality does not show" signature
  nyiso-84 recorded. E4 predicts it stays quiet on the repaired keeper; if
  it fires anyway, nyiso-84's objection stands and the arm dies on it.
* **P5 — forcing budgets:** any class crosses its rule-20 forced-share cap
  that did not already sit across it in the control (2024 ST_GAS sits near
  the 30 % line; peakers 15 %).

## 6. Verdict rules

* **KEEPER** only if: every K passes, no P fires, **C3a-2025 improves**
  (moves toward 0 from −9.64), no criterion verdict regresses — and the
  leave-one-year-out duty (rule 22) is discharged: with zero free
  parameters there is nothing to re-fit, so LOYO here is the reporting
  obligation that the arm's C3a movement is same-signed in each year
  standing alone (a mechanism that helps only one year's level while
  degrading another's is a level trade, not structure — it stays
  CANDIDATE).
* **CANDIDATE-REJECTED** if any P fires (registered with the fired gate
  named).
* **INERT (`I`)** if K3 fails (registered; the widening build inherits).
* Whatever the verdict, the amplitude / swing-share / formed-dual-vs-
  measured-spin comparisons are **REPORTED, never gated** — the rubric
  amplitude criterion is an OPEN OWNER CALL this pre-registration does not
  touch.

## 7. Pre-committed expected effects (the level story, both directions)

Adverse, expected, and not grounds for silent tolerance: **C3a-2023 rises**
(the un-cancellation; P1 is its hard ceiling). Helpful, expected: C3a-2025
rises toward band-center; peak-window formation concentrated in the E4
hydro-short hours. Neutral-to-small: C3a-2024 rises within band; C3c can
only improve or hold (prices weakly rise; the $775 RCPF ceiling cannot
reach $300+ from the shallow-shortfall steps — nyiso-84's depth result is
not contested). Dispatch side: reserve re-allocation away from idle GT
capacity onto online hydro/quick-start output; bounded GT dispatch increase
allowed only OUTSIDE the overnight window (P4 polices the window nyiso-84
flagged).

## 8. Memory / environment

The delta adds one family re-class + a class-2 eligibility row — no
(n_gen, T) overlay, so no swapfile is required (miso-113 note); years run
sequentially inside each invocation (rule 12), invocations run one at a
time (4 cores / 15 GB, per-plant LP).
