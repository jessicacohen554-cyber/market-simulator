# FINDING miso-114 — independent confirmation of the COAL_PRB night-floor `I` verdict, + the guard gap that let it happen twice

Session miso-114, 2026-08-03. **No run is registered by this session** (see §3).

## 0. What happened

This session was tasked with solving the miso-113 arm. It did so independently
and in parallel with the session that produced
`2026-08-02-miso-113b-night-floor`, without either being aware of the other.
Both sessions:

- independently discovered the SAME wiring defect — `miso_coal_night_floor` was
  threaded into `pipeline/year.py` and `runner.py` but not
  `scripts/run_calibration.py`, the orchestrator every calibration arm actually
  runs — and independently diagnosed it from the same three symptoms (no log
  line, no `MECH_MISO_COAL_NIGHT_FLOOR` id 22 in the floors sidecar, and a P1
  that warm re-solved the P0 model instead of cold-rebuilding on a floored
  fleet);
- fixed it, solved the arm, and reached **the same verdict: `I`, provably
  inert.**

**The already-merged adjudication stands and is not disturbed.** The matrix cell
is `I`; nothing here changes it.

## 1. The numbers agree independently

| statistic | merged run (2026-08-02) | this session | agree |
|---|---|---|---|
| floor volume 2023 / 2025 | 15.89 / 17.39 TWh | 15.892 / 17.388 TWh | ✓ |
| scoped tranches | 197 | 197 | ✓ |
| unit-hours floored 2023 / 2025 | 116,616 / 123,912 | 116,616 / 123,912 | ✓ |
| COAL_PRB energy delta vs control | 0.000 TWh all years | 0.000 TWh all years | ✓ |
| D-1 COAL_PRB cv_ratio | 0.466 / 0.475 / 0.314 | 0.466 / 0.475 | ✓ |
| night level, control | 0.4957 / 0.4482 / 0.5666 | 0.4957 / 0.4482 / 0.5666 | ✓ |
| C1 | 16/16, free 12/12 | 16/16, free 12/12 | ✓ |
| D-4 off-window | 0.0 | 0.0 | ✓ |

Two independently-built solves of the same recipe landing on identical numbers
is worth recording as a reproducibility datum in its own right.

## 2. Two things this session adds

### 2.1 The mechanical cause of the inertness, per tranche

The merged note gives two reasons (the keeper already sits above the measured
night level; the plant absorbs the floor internally). Measured per floored
tranche on the solved arm, the mechanism is sharper than that:

- **14 of 18 floored tranches have `floor / tranche_max` = 1.000.** The detector
  caps `target_mw` at the `_committed` tranche's own capacity, and at those
  plants the measured `night_p50 − mustrun_pct` EXCEEDS that capacity, so the
  floor is clipped to the **entire committed band** — which the LP already runs
  flat out under the regulated take-or-pay discount.
- The other 4 sit far below their tranche max (`floor/tranche_max` 0.011–0.273),
  non-binding by a wide margin.
- Direct floor-vs-dispatch on the arm's own output: **0 binding unit-hours and
  0.0000 TWh binding volume in all three years**, against 19.86 / 20.98 / 22.40
  TWh of headroom above the floor.

**Where the residual actually lives, and it is not the committed band.** PREREG
§5's K1 estimated 6.196 / 6.189 / 2.271 TWh of binding by comparing each
**plant total** against `night_p50 × nameplate`. That comparison is sound, but
it measures a different object than the mechanism constrains: the runtime floors
only the `_committed` **tranche**, capped at that tranche's capacity. In the
hours K1 counted, the plant is below its night level because its **`_econ` /
`_peak` tranches are OFF**, not because the committed band backed down — the
committed band is at its cap in every one of those hours. So K1's number should
not be re-quoted as a binding volume, and **any successor must act on the
`_econ`/`_peak` on/off pattern**, which no lever in the MISO queue addressed.

Corollary for the miso-111 re-reading: its "provably inert" verdict is
**half-vindicated**, not refuted. The **level** leg is genuinely refuted (the
night level does sit above the mustrun band at 18 of 26 REG plants, 69.2 % of
capacity). The **reachability** leg HOLDS — the committed band does not back out
below the floor in any hour of any year.

### 2.2 Solve-path memory: a floored MISO P1 does not fit in 15 GB

Two OOM kills at **16.00 GB and 15.96 GB anon-RSS** (`total-vm` 27.41 GB both
times), each while 2025's floored P1 was being built. Cause is at
`pipeline/solve.py:300-317`: a `p1_fleet_prep` floor forces P1 down the
**cold-rebuild** branch, which builds a second `DispatchModel`.
`MARKET_SIM_P1_FLOOR_INPLACE=1` was tried and **declined**, exactly as its
docstring says it does when availability feeds ramp/co-opt rows — MISO's
`miso_reserve_pergen` builds availability-scaled 10-min ramp caps, which a
P-column bound edit cannot reproduce.

Worked around without touching the recipe: 2025 solved in a fresh process with
no prior-year tables resident, then merged and re-assembled through
`--reuse-solved` (per-year config hashes re-verified: 2023 `2b9cf46624be944b`,
2024 `9e4a68dc4397cd9b`, 2025 `d68610680976cdcf`).

**Standing note: a MISO per-plant floored P1 is the largest floored LP in the
repo and needs > 15 GB, or a solve-path change. Budget for it before arming any
future MISO floor.**

## 3. Why no run is registered

`2026-08-02-miso-113b-night-floor` is already registered with the same verdict
and the same numbers. Registering a second, near-identical rejected arm would
consume one slot of MISO's top-15 retention and evict a distinct run to say
something the dashboard already says. Rule 15's purpose — results live on the
dashboard, not in chat — is served by the existing registration; this document
records the confirmation and the additive diagnostics. **The matrix cell is left
exactly as the merged session stamped it (rule 28: no re-test, no new verdict).**

## 4. The guard gap — fixed here (the durable deliverable)

`tests/unit/pipeline/test_p1_prep_wiring.py` exists precisely to prevent this
failure mode (it was written after nyiso-87, the identical bug). It did not
catch it, and the merged note says why: its `_BRIDGE_BUILDERS` roster is
**hand-maintained and did not carry the builder**. The merged fix adds the
missing row — which restores coverage for THIS bridge but leaves the mechanism
that failed fully intact for the next one.

Added here: `test_roster_is_complete_without_hand_maintenance`, which
cross-checks the roster against the source **by behaviour** — every `build_*`
call in an orchestrator is bound to the local name(s) it assigns, and any
builder whose local name reaches a `p1_fleet_prep=` chain in ANY orchestrator
must carry a roster row. Builders whose result only reaches `p1_kwargs_prep=`
(e.g. `build_caiso_reserve_p1_prep`) are excluded automatically, so there is no
allowlist to forget either.

**Verified against the exact original state** (bug present AND roster row
absent): all four pre-existing tests PASS and only the new one FAILS. That is
the gap, demonstrated closed rather than asserted.

It also immediately found a second, unrelated unrostered bridge:
**`build_pjm_reserve_p1_prep`**, whose fleet half reaches the `p1_fleet_prep`
chain in all three orchestrators but carried no roster row — i.e. the PJM
reserve bridge was itself unguarded against the nyiso-87 / miso-113 failure
mode. Its row is added.
