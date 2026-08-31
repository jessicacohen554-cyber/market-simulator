# FINDING miso-193 — `cc_duct_peaking` examined in MISO; the ~8% cap A/B (2026-08-31)

Session miso-193, chartered by the miso-192-corrected queue: take the first
named candidate off the keeper-armed-elsewhere-never-examined-here list
(`cc_duct_peaking`, K@NYISO, bare U in MISO) and run it end to end.

Keeper at session start and throughout Ask A: `2026-08-30-miso-191-bexit`
(bundle `results/calibration/miso191_bax_B`). Ask-A reproduction (zero-solve):
determination **NOT-YET at rubric v3.5 on {C3a-2025 −12.3405%} ALONE**; C1
16/16 / 12/12 free; C3c the single ledgered caveat; C6 attested; C8 PASS with
its two grounded above-budget report notes; `audit_keepers --iso MISO` PASS
0/0; `build_status --iso MISO --check` in sync; `check_mechanism_matrix.py`
integrity OK. All exactly as handed off.

## 1. Premise correction — the mechanism is ALREADY ARMED on the MISO keeper

The handoff charters `cc_duct_peaking` as un-armed in MISO ("replacing the
offer curve's class-wide pct_peaking with a published per-plant fact") with
the A/B arm = "`cc_duct_peaking` only". That premise is **stale**:

- `miso191_bax_B/run_config.json` records `cc_duct_peaking=True`,
  `cc_duct_peaking_cap_pct=None`, `cc_peaking_per_plant=True`. The mechanism
  has been the MISO **default** since the 2026-07 G-26/C-12 generalization
  (`pipeline/backcast_config.py` arms it for every ISO; only PJM also carries
  the 8.0 cap). Every current MISO keeper solve, miso-191 included, runs the
  duct map — **uncapped**.
- NYISO's K on this row is a **registration-K** (nyiso-115 shared-field
  census: "the NYISO cell records that the field is armed on NYISO's own
  designated keeper… Registration, not adjudication"). So "K@NYISO, U here"
  never meant "tested there, un-armed here" — it meant *registered there,
  never examined anywhere*.

Consequence: the handoff's A/B is value-identical to its own control and
impossible as a single delta. The genuinely untested delta — and the half of
the charter's own mechanism description ("capped at the F-class
supplementary-firing engineering maximum ~8%") that MISO does not run — is
**`cc_duct_peaking_cap_pct=8.0`**. The corrected charter was frozen ex ante
in the phase-0 probe docstring
(`scripts/probes/_miso193_duct_peaking_phase0.py`, commit `92847a8`, pushed
before any adjudicating quantity) and the A/B pre-registered in
`PREREG-miso193-cc-duct-peaking-cap-2026-08-31.md` (commit `71a9220`, pushed
before the arm existed).

Why the cap is the structurally-preferred variant (rules 1/14, not a fit):
the raw EIA-860 nameplate-vs-net-summer gap **conflates the ambient summer
derate with the duct-firing increment** (the field's own docstring). MISO
carries the ambient half in availability through the armed
`summer_derate_basis_aware` (miso-148), so sizing the expensive band from the
raw gap double-counts the ambient component in band *sizing*. 8.0 pp is the
F-class supplementary-firing engineering maximum — the identical physical
constant the PJM default carries — identified from engineering practice,
never from a residual (rule 21: the DOF ledger gains one non-residual
parameter).

## 2. Phase-0 census (zero-solve, rule frozen at `92847a8`)

Record: `results/calibration/_miso193_duct_peaking_phase0.json`. All
quantities derive from the exact bases the mechanism reads at solve time:
`fleet.cc_duct_peaking_pct()` (the EIA-860 Generator_Y Operable CC map) and
the load-bearing `load_fleet_from_csv → fleet_to_bins → bins_to_fleet` build
under the keeper's reconstructed `ScenarioConfig`.

- **A2 coverage: 100.0%** of the 34,706.5 MW MISO CC class (68/68 rows;
  CC_REGULAR 27,420.1 MW, CC_CHP 7,286.4 MW) is covered by the duct map —
  far above the frozen 50% line (the miso-141 §11.2 / miso-192 precedent).
- **41 duct-flagged rows, 18,659.3 MW** carry a positive band (gap p10 6.1 /
  p50 13.7 / p90 22.0 / max 32.0 pp); **27 explicit-zero rows, 16,047.2 MW**
  carry a 0 band — of which 22 rows / 724.8 MW of phantom class-default peak
  band is what the armed mechanism currently removes vs the no-duct
  counterfactual. Net vs no-duct: +1,425.2 MW of band grown on 29 rows,
  −763.1 MW shrunk on 25 rows.
- **A3 cap reach: 33 rows / 16,157.9 MW have gap > 8**; the 8.0 cap clips
  1,261.3 MW statically, **1,013.5 MW LP-realized** on the base-fleet build
  = 6.76% of flagged MW ≥ the frozen 1% line.
- **A1 liveness: 92.07% of covered MW conforms — FAILS the frozen 99% line.**
  Reported against interest and diagnosed in §3.

## 3. The A1 miss is a witness MIS-FREEZE, not a seam clobber (disclosed)

The frozen A1 relation assumed the unclamped identity
`peak_mw = capacity × duct_pct/100` for every covered row. The load-bearing
code documents two CHP steam-host mechanisms that legitimately supersede the
duct band on steam-following cogens:

1. **The committed-first clamp** (`assembly.py:630`): when the CAMPD-measured
   committed level plus the peak band exceeds the BTM-shrunk grid share,
   "committed keeps its measured level, the scarcity peak gives way."
2. **The steam-floor re-banding** (`assembly.py:827`): the measured
   steam-host floor shifts committed capacity into the econ slices that
   carry it.

Every one of the 10 deviating rows is CC_CHP and every deviation is fully
explained by this chain. Verified numerically on Sabine River Operations
(10789, 502 MW, duct 15.6): BTM pull-out leaves a 150.6 MW grid share;
pre-clamp committed 225.8 MW ≥ grid ⇒ peak → 0 at the clamp; the steam-floor
shift then re-bands 22.8 MW committed→econ — reproducing the emitted
127.7/22.8/0.0 (committed/econ/peak) exactly. On 9 of the 10 rows the peak
band is zero in ALL THREE legs (keeper / no-duct / capped alike): the duct
input is irrelevant there under any value, so nothing is being "clobbered" —
the steam host owns the band by design (rule 19, one mechanism per
phenomenon; the same reason `cc_mustrun_per_plant` excludes CHP groups).
The tenth (Lansing REO Town 58427) realizes a partial band that RESPONDS to
the duct input in the correct direction (keeper 8.69 / capped 5.99 / no-duct
3.30 MW).

**Amended adjudication (the miso-191 precedent — the frozen rule could not
fire clean, the amendment is disclosed, never silently applied): LIVE.** The
duct value reaches the load-bearing seam on 100% of CC_REGULAR MW (79% of
the class) and on every CC_CHP row with grid-share room. The deviating
population is 2,753.7 MW = 7.9% of covered MW, all of it steam-host-owned.
With A1 adjudged live, frozen A2 (pass) and A3 (6.76% ≥ 1%) charter the
cap A/B.

## 4. The A/B (PREREG §4–§5)

- Control `miso193_control_A`: byte-faithful `replay_keeper.py` of
  `miso191_bax_B`.
- Arm `miso193_cap_B`: same replay `--set cc_duct_peaking_cap_pct=8.0`.
- Directional prereg (frozen in phase 0, before any census quantity):
  C3a DOWN, confidence 0.8.

RESULTS — (filled after the legs complete; gates record
`results/calibration/_miso193_ab_gates.json`.)

## 5. Disposition

(Filled with the gates verdict: promotion / rejection / owner escalation,
the cell stamp, and the registered run ids.)
