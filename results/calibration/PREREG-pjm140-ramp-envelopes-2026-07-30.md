# PRE-REGISTRATION — pjm-140: `ramp_envelopes` on PJM (`ramp_limits = False → True`)

**Written and committed at pjm-139, BEFORE any arm solves.** Chartered by
`results/calibration/FINDING-pjm139-winter-morning-ramp-is-a-ramp-rate-deficit-2026-07-30.md`
§5. Nothing in this document may be revised after an arm has solved; if an
expectation is refuted, the refutation is recorded as such (the pjm-137
precedent, where the pre-registration was refuted on its own expected direction
and the delta was kept anyway on rule 14 grounds).

Matrix row `ramp_envelopes`, PJM cell **`U`** → this session's verdict.
Verdicts are per-ISO (rule 25): ERCOT's `R` and CAISO's `I` were reached on
**different defects** (the ERCOT coal dispatch-band pin; CAISO evening-CT volume)
and neither transfers. PJM derives its own artifact from PJM's own plants.

---

## §1 — the mechanism, and why it is admissible

`ScenarioConfig.ramp_limits` + `data.fleet.build_ramp_groups` +
`model/lp/rows.py::_build_ramp_rows`, fed by the frozen derive
`scripts/data/derive_campd_ramp_envelopes.py --iso PJM` (rule 23: run for PJM for
the first time, exactly as pjm-137 ran `derive_campd_ct_heat_rates.py --iso PJM`
for the first time — a new ISO's artifact, not a re-derivation against a
residual).

Per (facility, CC/CT/ST family) pooled over 2023–2025:
`ramp_up_mw` = the **max observed** 1-h increase in summed CAMPD gross load;
`ramp_dn_mw` = the max observed 1-h decrease **excluding trip-to-offline**
deltas. Facilities below `MIN_OBS_HOURS` fall back to the capacity-weighted
median class envelope *fraction*. The loader rebases CAMPD **gross** → model
**net** per plant (the ercot-132 leg A repair) and **prunes any group whose
envelope ≥ plant capacity**, so bang-bang CTs prune out by physics and no
class-name gate exists anywhere (rule 18 `[R-PHYSICS]`).

**Zero fitted degrees of freedom.** Every number is a measured maximum from the
CEMS trace. The DOF ledger gains one entry (the artifact) with `n_residual`
UNCHANGED. Rule 5 `[R-NO-MAGIC]`: no magic number is introduced. Rule 24
`[R-REGISTRY]`: `ramp_limits` is a declared `ScenarioConfig` field recorded in
`run_config.json`.

**Rule 14 `[R-ACCURATE]` is the charter, not the residual.** The keeper currently
asserts that every thermal plant can move from any output to any other output in
one hour. That is false as physics and false in the measured record. Replacing it
with the measured envelope is an accuracy correction and goes in on that basis.
**Rule 1 `[R-STRUCT]`: it stays in if it makes the fit worse**, and the root cause
is then pursued elsewhere.

**Rule 19 `[R-ONE-MECH]` reconciliation.** No other mechanism in the PJM keeper
owns intertemporal thermal coupling: `ramp_limits=False`, `commitment_enabled=False`,
`pjm_commitment_posture=False`, `committed_ramp_spread=0.0`, and the three P1-native
commitment bridges are all ISO-exclusive to CAISO/ERCOT/NYISO. `measured_ramp_capability=True`
governs **reserve ramp eligibility**, not energy ramping. So this is a new
phenomenon with a single owner, not a second mechanism stacked on an existing one.

## §2 — the defect, pre-sized (from `FINDING-pjm139`)

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| DJF h04 → h07 rise, measured MEC | +15.28 | +21.63 | +35.45 |
| DJF h04 → h07 rise, model | +3.93 | +4.55 | +6.51 |
| model as % of measured | 26 % | 21 % | 18 % |
| DJF h06–h07 reachable residual, CT-wtd (after basis + reserve credits) | 3.93 | 30.48 | 40.11 |
| DJF h06–h07 reachable residual, load-wtd | −0.37 | +5.55 | +13.44 |

**The pre-registered ceiling.** 2023's DJF morning residual is already
**negative** after the two closed lanes are credited — there is nothing there to
close, and a delta that "improves" 2023's morning ramp price is moving a number
that is already explained. The claimable target is **2024 and 2025 only**, and it
is bounded by **+$5.55 / +$13.44 /MWh** load-weighted in the DJF h06–h07 window.
A delta reported as closing more than that is measuring something else.

## §3 — the pre-check that has already fired (no LP, `FINDING-pjm139` W7)

p99 1-h up-move as a fraction of each side's own fleet peak, model ÷ actual:
**CC 1.42 / 1.72 / 1.53**, **CT 1.38 / 1.70 / 1.52**, **ST 1.61 / 1.62 / 1.50**.
Aggregate excess proves per-plant binding (the aggregate is the sum of the
parts); the test is one-sided and cannot prove inertness.

## §4 — EXPECTED DIRECTION, pre-registered

**Primary (the one this is judged on): the DJF h04 → h07 model price rise
INCREASES**, toward the measured +$15.28 / +$21.63 / +$35.45. Mechanism: capping
the steam and CC families at their measured hourly move removes the cheap supply
the model currently uses to meet the morning ramp, so the clearing point moves up
the stack onto CT tranches.

**Secondary, all pre-registered as expected consequences, none of them the
justification:**

1. **`CT_PEAKER` volume RISES.** `FINDING-pjm139` §5.2 measures the model ramping
   CTs at only 58 / 76 / 83 % of the real fleet's winter morning rate. ISO-wide
   `CT_PEAKER` |err| is currently 2.11 / 3.57 / 3.32 TWh short, so this is
   expected to *improve* C1's CT row and to move `COAL_BIT` / `CC_REGULAR` the
   other way. **C1 must still pass 16/16 with free 12/12** (kill K2 below).
2. **The overnight over-pricing does NOT improve, and may worsen slightly.** A
   down-ramp envelope keeps units online overnight that the model currently shuts
   down — which adds cheap inframarginal energy and would push the overnight
   price *down* toward PJM's (helpful) — but it can equally hold *dear* units on
   (harmful). The direction is genuinely ambiguous and is pre-registered as
   ambiguous rather than guessed. This is **not** the lever for §W4's
   bottom-of-distribution miss and is not claimed as such.
3. **C3c tail hours RISE.** Forcing CTs on at a winter cold-snap morning is
   exactly what C3c counts. **This is the risk direction, not a benefit** — C3c
   currently passes by ~1 h (2024) and ~2.5 h (2025) against a **0.5× floor**,
   and it has an upper bound too. See kill K3.
4. **C8 `CT_PEAKER` forced share** may move. It is currently 16.3 / 16.9 / 17.1 %,
   all GROUNDED. A ramp row is **not** a min-gen floor and adds no D-2
   mechanism id, so forced energy should be ~unchanged; if it moves, the D-2
   attribution must explain why.

**Explicitly NOT expected, and pre-registered as such:** this delta does **not**
address the basis/congestion half of the Dominion CT deficit (pjm-137, closed),
does **not** address the reserve opportunity cost (pjm-138, closed), and does
**not** address the annual price level (already correct to +$0.47/+$2.62/+$8.48).
It is a **shape** delta and must be judged on shape.

## §5 — NO-FEEDBACK CEILING (binding, rule 13 / rule 21 / rule 23)

The derived envelopes may **never** be multiplied, scaled, haircut, blended,
floored, capped, widened, tightened, per-plant overridden, quantile-swapped
(max stays max) or scarcity-exempted. The only admissible knob is the flag's
on/off state. If the measured envelope produces a bad result, the finding is
recorded and the root cause pursued elsewhere — the envelope is not tuned. The
derive is re-run only when CAMPD data updates, and any re-derivation commit must
cite the data change (rule 23 `[R-FROZEN-DERIVE]`).

Rule 25 `[R-ISO-SCOPE]`: the artifact is PJM's, derived from PJM plants, written
to `campd_ramp_envelopes_PJM.csv`. It never touches another ISO's cell, and a PJM
verdict never fills one.

## §6 — PRE-REGISTERED KILLS

The delta is **REJECTED** if any of these fires. Each is checkable and none is
negotiable after the fact.

- **K1 — inert.** If arm B's dispatch differs from arm A's by < 0.1 % of class
  energy in every class and every year, the mechanism is measured INERT on PJM
  (the ERCOT-127 outcome, where the real fleet violated its own envelope 0–10
  times a year). Record `I`, do not tune the envelope to make it bind.
- **K2 — C1 breaks.** Any C1 band failure, or free-band count below 12/12.
  The mix must be right (rule 1).
- **K3 — C3c breaks in EITHER direction.** C3c has a 0.5× lower floor *and* an
  upper bound. 2024 is at 10 h against RT 18 h and 2025 at 32 h against 59 h;
  if the delta pushes the count above the upper bound, that is a fail, not a
  triumph.
- **K4 — slack or dump appears.** A ramp constraint can make the LP unable to
  serve load. ZERO slack and ZERO dump in both arms, all years, or the envelope
  is infeasibly tight and the artifact is wrong.
- **K5 — the control arm is not byte-identical.** Arm A must reproduce
  `pjm137_ctheatrate_B` to 0.000000000 MW over 166,440 class-hours per year.
  Anything else invalidates the A/B.
- **K6 — the primary moves the wrong way.** If the DJF h04→h07 model rise
  *falls*, the mechanism is refuted on its own charter — record it and stop.
- **K7 — a pruning artifact.** If the loader prunes so aggressively that fewer
  than half the ISO's thermal capacity carries a live envelope, report the
  pruned share explicitly before any verdict; a mechanism that only binds on a
  sliver is not a fleet-level ramp representation.

## §7 — OPERATIONAL RISKS to measure before committing a three-year arm

1. **LP memory is the live risk and is UNQUANTIFIED.** A PJM per-plant year-solve
   already peaks at 14.8–15.2 GB on a 15 GB box with 8 GB swap. Ramp rows add
   `2 × n_ramp_groups × (T−1)` rows. **Solve ONE year first**, record the peak
   RSS, and only then launch the three-year arm. If one year does not fit, say so
   and stop — do not silently drop to a shorter horizon (rule 16 requires all
   three years in one bundle for a keeper).
2. **The artifact does not exist yet.** `derive_campd_ramp_envelopes.py --iso PJM`
   needs `data/clean/` (it calls `load_fleet_from_csv`). Budget the full
   `regenerate_clean.py` first.
3. **Report the derive's own coverage**: plants enveloped, plants on the class
   fallback row, groups pruned as non-binding, and the gross→net rebasis factors
   applied — the pjm-137 disclosure pattern.

## §8 — A/B protocol

```
# arm A — the control. NO --set: reproduces pjm137_ctheatrate_B byte-identically.
scripts/replay_keeper.py results/calibration/pjm137_ctheatrate_B \
  --out-dir results/calibration/pjm140_control_A \
  --note "pjm-140 control: pjm137_ctheatrate_B recipe verbatim, zero delta"

# arm B — the single delta.
scripts/replay_keeper.py results/calibration/pjm137_ctheatrate_B \
  --out-dir results/calibration/pjm140_rampenv_B --set ramp_limits=True \
  --note "pjm-140: ramp_limits False->True on the measured PJM CAMPD ramp envelope"
```

Arms SEQUENTIAL (rule 12), years sequential within each (rule 16), `swapon
/swapfile` re-asserted before each arm, launched with `setsid nohup`.

**A control arm with no `--set` inherits the keeper's `meta.timestamp` DATE —
patch `meta.json`'s timestamp to the real solve date BEFORE `dashboard_add_run`.**

Post-solve, in order: `legitimacy_diagnostics.py --bundle <arm> --iso PJM --years
2023 2024 2025 --json-out <arm>/legitimacy_diagnostics.json --report
<arm>/legitimacy_report.md` (the `--json-out` is REQUIRED or C7/C8 have no
committed contract) → a `gen_pjm140_attestation.py` copied from
`gen_pjm137_attestation.py` (without `calibration_attestation.json`, C6 reads
UNATTESTED) → `dashboard_add_run.py --label "pjm 140 rampenv" --bundle <arm>` for
**both** arms → `calibration_verdict.py --run-id <id>`. PJM is at the 15-run cap,
so registering two arms prunes the two oldest. Update the `ramp_envelopes` matrix
cell in the same session, rejected outcomes included (rule 28 duty b).

**Keeper promotion is owner-only.** Recommend; never self-promote.
