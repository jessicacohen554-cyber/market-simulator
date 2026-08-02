# FINDING miso-113 — the COAL_PRB night floor is LIVE-INERT; K1's licensing measurement was an outage-window artifact

Session miso-113 Phase 3 (arm execution), 2026-08-02, branch
`claude/next-lane-cross-iso-queue-q1x2ux`. Phases 1–2 and the kill/guard
pre-registration: `PREREG-miso113-prb-night-floor-2026-08-01.md` (committed
pre-measurement, pre-solve). K1 did not fire (§8) and Phase 3 was licensed;
this doc records that the SOLVE returns the verdict K1 was designed to reach
without one — the mechanism is inert — and diagnoses why K1's construction
missed it.

## 0. Verdict

**`I` — provably inert in the live LP, adjudicated on the full-span A/B.**
The floor is written exactly as designed (detector, per year: 197 scoped
tranches; 15.892 / 15.413 / 17.388 TWh of floor volume over 116,616 /
115,320 / 123,912 unit-hours; 97 / 79 / 85 committed blocks, none shorter
than 24 h) and moves NOTHING any gate can see:

| year | COAL_PRB class-hourly L1 vs control | share of class energy | annual TWh | D-1 cv_ratio |
|---|---|---|---|---|
| 2023 | 12.7 GWh | 0.010 % | 123.690 → 123.690 | 0.466 → 0.466 |
| 2024 | 11.5 GWh | 0.010 % | 118.327 → 118.327 | 0.475 → 0.475 |
| 2025 |  9.0 GWh | 0.006 % | 147.137 → 147.137 | 0.314 → 0.314 |

Every C-criterion record status is identical to the control (zero flips
across C1/C2/C3a/C3b/C3c/C4/C7/C8); C1 stays 16/16 free 12/12; the
miso-112 §4 night-level structural test is IDENTICAL to the control
(cap-weighted model level 0.4957 / 0.4482 / 0.5666 vs measured 0.4343, error
unchanged to 4 decimals). NOT a keeper candidate: no gate moves and no
structural statistic moves — there is nothing to weigh under the owner's
structural-integrity standard. Keeper UNCHANGED
(`2026-07-31-miso-109b-hy-level`).

## 1. Arms

- **A (control)** `results/calibration/miso113_control_A` →
  `2026-08-01-miso-113a-control` (keeper recipe at HEAD, no delta;
  registered by the Phase-1/2 session).
- **B (arm)** `results/calibration/miso113_nightfloor_B` →
  `2026-08-02-miso-113b-night-floor` (A + `miso_coal_night_floor=true`),
  solved this session via the committed rule-12 chain
  (`scripts/probes/_miso113_chain.sh`, one fresh year per process,
  `--reuse-solved` links).

HEAD equivalence: control solved at `247e795`, arm at `9037ee7` (main
`a92ae97` + the wiring fix below, merged as PR #3266); the src delta between
the two solve trees is ERCOT-only default-off (ercot149 gas event cap),
forecast-mode-only (FFR-1D schedulable gates), non-solve (probes/docs), or
the flag-gated wiring fix itself — every arm movement is attributable to the
single flag. D-2 skew tripwire: the arm's rebuilt `reliability_floor` rows
are byte-identical to the control's (0.5453 / 0.5858 / 0.3873 TWh).

## 2. Operational incident — the mechanism was not wired into the backcast orchestrator (fixed this session, PR #3266)

The first arm launch produced a 2023 solve BYTE-IDENTICAL to the control
(class-hourly L1 = 0.000 GWh) with `scenario_config.miso_coal_night_floor =
true` recorded in its run_config and no detector log line — the nyiso-87
failure mode verbatim. Root cause: `build_miso_coal_night_floor_p1_prep` was
composed into `pipeline/year.py` and `runner.py` but never into
`scripts/run_calibration.py`'s own `p1_fleet_prep` chain — the third
`run_energy_solve` call site and the one every calibration arm actually
solves through. The three-site guard
(`tests/unit/pipeline/test_p1_prep_wiring.py`) exists for exactly this, but
the miso-113 build session never added the new builder to its
`_BRIDGE_BUILDERS` roster, so the guard was blind. Fix (commit `9037ee7`):
import + build + compose the hook in run_calibration.py, and add the roster
row so the import/call/chain assertions cover the MISO hook — and every
future bridge — in all three orchestrators. The broken partial solve was
deleted and the chain relaunched from scratch on the fixed code.

## 2.1 Operational note — the ARM's 2025 link OOMs a 15 GB box; swap is the fix

The chain's 2025 link (fresh 2025 + two byte-copied years) was OOM-killed
twice at the box ceiling (~15.17 / 15.19 GiB anon-RSS, kernel oom-kill),
both times DURING the P1 solve — the control's same link fit on 2026-08-01.
The arm's retained delta at solve time is the floored-fleet composition
(`_bridge_floored_fleet`: fresh `min_gen` + `availability` + mechanism
copies ≈ 0.4 GiB) on top of a control peak already near the ceiling; the LP
itself is memory-identical (a min-gen floor changes variable bounds, no new
matrix nonzeros). `MALLOC_ARENA_MAX=2` alone was not sufficient. Resolution:
a 6 GB swapfile (the container permits `swapon`), absorbing the overage
without touching solver options or the solve path. Carry-forward for MISO
arm sessions that add any (n_gen, T) overlay: enable swap BEFORE the 2025
link.

## 3. Why the floor binds nothing — the K1 construction was availability-blind

K1 (prereg §5/§8, probe `_miso113_floor_binding_audit.py`) measured 6.1957 /
6.1893 / 2.2705 TWh (2023/24/25) of deficit below
`floor_mw = min(night_p50, mustrun+committed) × NAMEPLATE` over online hours
of the keeper's per-plant payload — 10× the 0.5 % inertness line — and
licensed the solve. Reproduced exactly this session (6.1956 TWh vs the
control payload, 2023). Decomposition against the arm's own committed floor
arrays (`floors/2023_P1.npz`) and per-unit dispatch:

1. **The deficit hours are OUTAGE WINDOWS, not nights.** Across the four
   plants carrying 5.0 of the 6.2 TWh (1733, 1710, 56068, 1893), the
   deficit hours' hour-of-day distribution is UNIFORM — night (h0-5) share
   0.25 / 0.25 / 0.25 / 0.33 vs 0.25 uniform — and they arrive as
   whole-month blocks in shoulder months (plant 1710: October = all 744
   hours). The keeper's dispatch in those hours sits below even the plant's
   MUSTRUN band alone (1733: 925 MW vs a 1,407 MW band; 1710: 562 vs 798;
   56068: 486 vs 660), which — since the fuel-free mustrun tranche always
   dispatches its full available capacity — is possible only under
   unit-outage derates. K1 measured `nameplate − availability`, not a night
   backdown: its floor basis ignored `availability[g,t]`, which the
   keeper's armed outage machinery (5-day windows + short windows + maxgen
   events) derates heavily in exactly those blocks.
2. **The net-of-mustrun level at the deficit plants is ~zero.** The rule-19
   reconciliation (`frac = max(0, night_p50 − mustrun_pct/100)`, prereg §3)
   nets each plant's own mustrun band out of the written floor, and at the
   deficit-carrying plants the band nearly equals the night level: 1733
   0.459 vs 0.464 → ~5 MW written; 1710 0.600 vs 0.625 → ~15 MW; 56068
   0.519 vs 0.579 → ~30 MW. 91.9 % of the K1 deficit volume falls INSIDE
   hours where the mech-22 floor was written — written at these near-zero
   levels, already satisfied by the control dispatch.
3. **The floor therefore eliminates none of the K1 statistic** (6.1956 →
   6.2145 TWh, arm vs control on the identical construction) and the class
   total does not move.

The two effects are the same fact seen twice: the measured `night_p50` is a
level the fleet holds WHEN AVAILABLE, and the model already holds it — the
take-or-pay-discounted mustrun+committed block sits at that level in every
available hour. What the model lacks (C7's CV miss) is the fleet's
within-run DOWNWARD cycling — variance a min-gen floor cannot create, only
remove. Prereg P-A said exactly this ("its first-order effect on within-day
CV is therefore negative… if this arm improves C7 it must be through a
second-order price-formation channel"); with ~zero binding volume even that
channel is void.

**miso-111 PREREG §8's "provably inert" verdict is thereby REINSTATED on its
conclusion with corrected grounds**: not because the LSL sits below the
mustrun band (the level argument prereg §4 refuted), but because the
regulated committed block is already pinned inframarginal at the night level
in every available hour, so a floor at that level has nothing to hold up.
Prereg P-C predicted inert-without-a-solve; K1's availability-blind
construction spent the solve to reach the same verdict.

## 4. Guard readout (pre-registered, prereg §6)

| guard | result |
|---|---|
| G1 C7 2023+2024 cv_ratio ≥ 0.5, profile_r ≥ 0.8 | **FAIL — unchanged** (0.466 / 0.475): the mechanism is inert, not shape-moving |
| G2 C1 16/16 every year, COAL_PRB ±8, no other flips | PASS — nothing moved (+2.02 / +1.86 / vintage-gap +1.28) |
| G3 COAL_BIT untouched (cv ≤ 2.0, r within 0.05) | PASS — identical (0.719 / 0.600 / 1.120) |
| G4 C3a/C3b/C3c no verdict flip | PASS — zero record-status flips |
| G5 C8 ≤ 30 % or grounded; D-4 ≤ 0.05 | PASS — night-floor D-2 rows 1.34 / 2.51 / 0.53 % of COAL (dispatch-at-floor accounting; the LIFT vs control is ~0.01 %); D-4 off-window 0.000, pass |
| G6 registration + matrix | this session: `2026-08-02-miso-113b-night-floor` registered; matrix cell M `O → I` |

P-B (the 2023 C1 over-band risk) is MOOT — the floor adds no energy. The
honest cell verdict is `I`, not `R`: no pre-registered kill fired against a
live effect; there is no live effect.

## 5. The lane after miso-113

C7 COAL_PRB queue state: the offer-side family is spent (miso-111 `R`,
miso-112 `R`) and the floor side is now `I` on live-solve evidence. The
within-run cycling variance the gate wants is downward flexing of a block
that the market design (regulated self-commitment + take-or-pay) and the
model both hold flat at the night level; no in-model min-gen or offer lever
remains chartered. Surviving routes per matrix §5.4: the contract-tonnage LP
constraint (RHS data-blocked — the Form 580 count is the bounded next step,
`miso-coal-contract-tonnage-data-ask-2026-07.md` §8) and the 2025 overnight
price-formation defect (data-blocked, miso-78/79). Until one of those data
asks lands, C7 COAL_PRB is a DIAGNOSED structural limitation with an empty
in-model lever queue.

## 6. Rule duties discharged

- Rule 15 [R-DASHBOARD]: arm registered `2026-08-02-miso-113b-night-floor`
  (full span, this session); retention pruned
  `2026-07-27-miso-98a-sectorabsent-control` (top-15 MISO).
- Rule 26 [R-MECH-MATRIX] duty b: `miso_coal_night_floor` cell M stamped
  `O → I` + evidence, §5.4 queue head adjudicated (this session).
- Rule 16/22 [R-ALLYEARS / R-HOLDOUT]: `--year 2023 2024 2025`, one bundle
  per arm, years sequential, no holdout year touched.
- Rule 21 [R-DOF]: no free parameter added; the mechanism stays merged,
  default-off, its three-site wiring now guard-enforced.
