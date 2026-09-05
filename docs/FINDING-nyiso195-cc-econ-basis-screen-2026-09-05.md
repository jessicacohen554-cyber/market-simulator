# FINDING nyiso-195 — the `CC_REGULAR` econ ramp at its own measured marginal heat-rate basis: phase 0 refutes the marginal-slice parking premise, the 2024 screen confirms it and is KILLED on E-3 (2026-09-05)

**Owner instruction under test** (in session, 2026-09-05, verbatim): *"Only run 2024
to see if it fixes the c1 gas cc miss. C3c is an acceptable caveat and known limitation of
this model type."* and *"No control arm just use the last keeper."*
**Keeper / control:** `2026-09-05-nyiso-192-astoria-panel` (rule 29(b) form 4; G-DRIFT
`d5bba63b..HEAD` all INERT — PREREG §4). **Pre-registration:**
`results/calibration/PREREG-nyiso195-cc-econ-basis-screen.md`, pushed at `9a0b80fe` before
the screen was launched, with the phase-0 prediction written in it. **Keeper unchanged. No
full span solved. Nothing registered** (rule 29: the screen bundle
`results/calibration/nyiso195_screen_2024` is a local throwaway probe).

## 1. Answer to the owner's question

**No. The arm does not fix the C1-2024 gas-CC miss; it worsens it.** Scored at the
scorer's own construction (`calibration_verdict.score_fuelmix` on the keeper's committed
payload with the screen's class-energy deltas applied):

| C1-2024 | keeper | screen |
|---|---|---|
| `CC_REGULAR` | +3.68 TWh, share +3.0 pp — FAIL (share) | **+4.34 TWh, share +3.5 pp — FAIL (volume AND share)** |
| `CC_CHP` | +2.10 TWh, +1.7 pp PASS | +1.66 TWh, +1.4 pp PASS |
| `ST_GAS` | −1.43 TWh, −1.0 pp PASS | −1.52 TWh, −1.1 pp PASS |

The sign was fixed before the solve by the arithmetic (PREREG §1, §3): under the armed
`gas_offer_net_revenue_margin` the econ ramp is the ONLY `CC_REGULAR` band that carries a
markup (committed 0.90 < phys 0.964 and peak 2.25 == phys 2.25 already clip to 0), so
offering it at its physical basis is a pure price CUT on every slice — 4.03 $/MWh at the
bottom, 2.10 at the top — on a class that already over-runs by 3.7 TWh. An LP never
dispatches less of a unit whose offer falls. The measured effect: `CC_REGULAR` +0.66 TWh
(37.99 → 38.65), taken from `CC_CHP` −0.45, `ST_GAS` −0.09, `CT_CHP` −0.04, `ST_CHP` −0.04;
the gas family is unchanged (68.22 → 68.25 TWh) and imports move 0.01. The phase-0 upper
bound was +0.95 TWh (74,783 newly-in-the-money slice-hours); the LP realised 69 % of it.

## 2. Phase 0 — the premise handed forward by nyiso-194 §3 does not hold (zero LP)

`scripts/probes/nyiso195_econ_basis_phase0.py` → `_nyiso195_econ_basis_phase0.json`, on the
keeper's committed artifacts only (on-recipe `fleet_only` rebuild, payload-decoded
per-plant hourly MW, `hourly/system_2024.parquet`, the band sidecars, CAMPD unit hourly).

**The keeper's econ ramp is priced flat.** The falling fixed markup (4.03 → 2.10 $/MWh
across the six slices) cancels the rising fuel-scaled physical basis (0.796 → 0.913 × base
HR) almost exactly: top minus bottom slice **$0.25/MWh**. That is why the committed 2024
band sidecar carries 2.782 … 2.801 TWh in each of the six slices (top/bottom 1.007): the
ramp switches on and off as a block, and "the marginal slice" is a rare state.

**Where the 80–90 % hours actually sit** (28,778 class plant-hours in 2024):

| position of the plant in its 80–90 % hours | plant-hours | share |
|---|---|---|
| at the top of its AVAILABLE econ ramp (the wall after unit-outage / derate availability) | 20,672 | **71.8 %** |
| above the available wall — partial duct (peak-band) dispatch | 7,897 | 27.4 % |
| mid-ramp on a marginal econ slice | 209 | **0.7 %** |

The static wall (`1 − pct_peak`) at Bethlehem 2539 / CPV 56940 / Astoria II 57664 is 0.910 /
0.849 / 0.831 of pmax; the availability-weighted wall the plants reach averages 0.841 /
0.734 / 0.729, and 4,288 / 4,075 / 2,998 of their 80–90 % hours are exactly there. **A plant
already at the top of its ramp cannot be moved up it by making the ramp cheaper, and the
band above it (peak, `phys_peak == peak`) is untouched by this delta.** So the econ ramp's
shape is not what places the class in 80–90 %; nyiso-194 §3's reading ("the LP parks each
plant where its econ ramp's marginal slice meets the LMP") was an inference from the two
killed arms, not a measurement, and phase 0 measures it false.

**CAMPD ramp-slope sign** (heat vs gross load, 50–95 % of each plant's own p99.5, quadratic
incremental fit): 10 of 14 fitted plants show a marginal heat rate that rises with load;
cap-weighted marginal / average-full-load HR 0.833 at 55 % → 1.056 at 92 %. The SIGN of the
registered `phys_econ_low 0.784 → phys_econ_high 0.925` ramp is confirmed; no level is
re-derived (rule 23) and none enters the arm. (Note for the nyiso-194 record: the phys ramp
does not "slope the other way" from the registered 0.95 → 1.0 — both rise with load; what
falls with load is the *markup*, i.e. their difference.)

**Footprint / screen year.** Econ-slice energy 14.47 / **16.76** / 15.76 TWh (2023 / 2024 /
2025) — the delta reprices the whole block, so 2024, which is also the year the owner named.
(The marginal-slice hours, had they been the object, are largest in 2023: 3,441 / 1,009 /
2,812 h, 0.17 / 0.04 / 0.16 TWh — 0.1–0.5 % of the block in every year.)

## 3. The 2024 screen (`scripts/probes/nyiso195_screen_gates.py` → `_nyiso195_screen_gates.json`)

Control side = the keeper's committed rows (`_nyiso194_screen_gates_S.json` keeper values,
the same per-plant construction; `hourly/system_2024.parquet`; the committed payload + bench
part) and zero-LP `fleet_only` rebuilds of BOTH bundles. No control solve. Environment
note (G-CTRL): the replay ran on pyarrow 24.0.0 / pydantic 2.13.4 against a keeper solved on
25.0.1 / 2.13.5 — both bundles' fleets rebuild byte-identically outside the delta (E-1), so
the comparison stands on the keeper's committed numbers.

- **E-1 footprint — PASS.** 0 tranche-pmax changes on the 809 LP units (screen fleet parquet vs
  the keeper rebuild: max |Δ| 0.0); heat rate, `offer_markup_hr` and `mc_base` change on
  exactly the **96 `CC_REGULAR` econ rows** (all of them, none other); every other class's
  offer bands identical; the arm's `CC_REGULAR` dict carries only the two changed keys.
- **E-2 identity — PASS.** Arm `offer_markup_hr` = 0 on all 96 slices; arm `mc_base` =
  keeper `mc_base` − `markup_k × anchor_k` hour for hour (max |err| 2e-5, float32); arm slice
  heat rate = `phys_k × base_HR` exactly; non-econ rows' `mc` byte-identical (max |Δ| 0.0).
  Fixed margin removed, cap-weighted: 4.22 $/MWh bottom / 2.20 top.
- **E-3 direction — FAIL, the frozen STOP (as predicted in PREREG §3).** Class MW-weighted
  loading shares, keeper → screen (CAMPD): **80–90 % 33.0 → 33.5 (16.5)**, 90–100 % 19.8 →
  19.6 (33.9). Neither moves toward CAMPD. Bins 0–100 %: keeper
  `[0.5, 2.0, 5.5, 6.4, 8.6, 4.5, 11.8, 8.0, 33.0, 19.8]`, screen
  `[0.5, 1.6, 4.1, 6.5, 8.8, 4.8, 12.2, 8.4, 33.5, 19.6]` — the mass that moved came from
  the 10–30 % bins up onto the ramp/wall, exactly the "hours below the ramp move UP to it"
  mechanism. Wall plants (57664 / 56940 / 54574 / 50292): hours above the old wall 2,199 →
  2,093 (CAMPD 12,935); mean 80–90 % share 32.9 → 33.8 (CAMPD 16.0). Peak-tranche energy
  1,253 → 1,232 GWh, tranche-hours 20,745 → 20,286 (the cheaper econ block displaces a
  little duct firing elsewhere in the class). Per plant the shape barely moves: 2539 80–90 %
  74.9 → 77.9 %, 57664 61.5 → 63.2 %, 56940 66.4 → 68.0 %, 56196 37.3 → 37.3 %; the energy
  lands at Cricket Valley 57185 (+181 GWh), 55405 (+158), 2539 (+145), 7314 (+114) — the
  plants phase 0 named.
- **E-4 companions — no flip.** Load-weighted mean RT price vs actual −0.72 % → −1.63 %
  (same-weights construction, in band); monthly NRMSE 0.183 → 0.181; gas-family volume
  68.22 → 68.25 TWh. The keeper row reproduces the nyiso-194 numbers exactly.
- **C8 (reported):** `CC_REGULAR` forced share 0.4 % (`nyiso_gas_commitment_bridge` 0.14 of
  36.7 TWh); the keeper's own D-4 rider rows are carried unchanged; D-2 passed.
- **C3c:** reported as an accepted caveat per the owner (this session), not a gate.

## 4. What this closes and what it locates

- **The econ-basis direction is REJECTED for NYISO** (rule 29 STOP on E-3; and rule 1 — the
  one residual it moves, C1-2024, moves the wrong way). The registered `CC_REGULAR` curve
  (0.90 / 0.95 → 1.0 / 2.25 with the `phys_*` basis under `gas_offer_net_revenue_margin`)
  stays as armed on the keeper. This is not the run-28 result re-run: run-28 (2026-06-25)
  re-grounded all three bands to the bare marginal HR *without* the margin mechanism and
  cratered C3a −24 %; here only the econ markup goes and C3a-like moves −0.9 pt — the
  mechanism's markup on this band is worth ~$3/MWh and ~0.7 TWh, not a price regime.
- **The whole `CC_REGULAR` offer lane is now adjudicated in NYISO's own lane on measured
  objects:** peak wall price up (nyiso-194 D, R), peak wall placement (nyiso-194 S, R), econ
  ramp basis (this session, R). None of the three moves the 80–90 % mass, because phase 0
  now shows where it is: **at the top of the AVAILABLE econ ramp**, i.e. the product of
  (i) the wall placement — the 860 nameplate-minus-net-summer gap sizing the duct band
  (nyiso-194 §1: 16.9–28.2 % vs CAMPD reach 0.6–5.8 %) — and (ii) the unit-outage / derate
  availability that lowers the wall a further 5–12 points of pmax at the pile-up plants. An
  8 % cap on (i) alone was killed because the plants then parked under the NEW wall
  (nyiso-194 S-3); the next measured object is therefore the availability side of the
  wall — whether the partial-derate / outage series applied to these CC plants (the
  `-perunitmerit-` extract, the temp-dependent derate) reproduces CAMPD's own hours above
  90 % (30,068 / 33,972 / 30,226 plant-hours vs the model's 20,677 / 29,532 / 31,276), a
  rule-14 data question with zero DOF, not an offer-curve lever. Handed to the §5.5 queue
  as (U); NOT run here.
- **The C1-2024 `CC_REGULAR` over-run is not an offer-level object in the econ band.** With
  the econ ramp flat within $0.25/MWh and the class dispatching as committed-plus-block, the
  over-run (+3.7 TWh, 24 % of it at Cricket Valley alone: 5,038 vs 4,241 GWh) is a
  commitment / online-hours object — the keeper keeps the class online 111 k plant-hours
  vs CAMPD 91 k (nyiso-194 phase 0) — which the owner-court D-2 unit-grain card already
  names. Nothing in this session changes that card.

## 5. Disposition

- **No keeper candidate from nyiso-195.** Keeper `2026-09-05-nyiso-192-astoria-panel`
  unchanged (NOT-YET; `complete` / `frontier` withdrawn, Q5 uniform rule).
- Matrix NYISO shard: `offer_curve_by_group` (econ-basis direction R, this citation; cell
  K for the registered curve) and `gas_offer_net_revenue_margin` (the econ-band markup's
  removal tested and R; cell K) annotated; §5.5 queue item closed and the availability-side
  object queued (U).
- **Cost:** one one-year screen (~35 min LP), two zero-LP rebuilds; zero full-span solves;
  zero control solves.

*(nyiso-195, 2026-09-05. Records: `results/calibration/PREREG-nyiso195-cc-econ-basis-screen.md`,
`_nyiso195_econ_basis_phase0.json`, `_nyiso195_screen_gates.json`,
`scripts/probes/nyiso195_econ_basis_phase0.py`, `scripts/probes/nyiso195_screen_gates.py`.
Screen bundle `results/calibration/nyiso195_screen_2024` local, never registered.)*
