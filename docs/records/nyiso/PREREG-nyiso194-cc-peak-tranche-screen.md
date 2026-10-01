# PREREG nyiso-194 — the `CC_REGULAR` duct-burner peaking tranche: phase 0 and two one-year screens (2026-09-05)

Pre-registration frozen and pushed BEFORE any solve. Owner ruling (in session
2026-09-05, verbatim): *"Promote it and then tune the cc regular offer curve up for
the duct burner peaking tranche because it's merit order is wrong it runs more
often at lower CF and is running hot over 80% CF in all years."* Keeper (the
control, rule 29(b) form 4): `2026-09-05-nyiso-192-astoria-panel`, bundle
`results/calibration/nyiso192_astoria_panel`, solved at `d5bba63b`.

Phase 0 (zero LP): `scripts/probes/nyiso194_cc_peak_phase0.py` →
`results/calibration/_nyiso194_cc_peak_phase0.json`; the revealed-price companion
`results/calibration/_nyiso194_duct_revealed_price.json` (inline computation,
same CAMPD/MIS inputs).

## 1. What phase 0 measured (the owner's two claims, at full magnitude)

Model = the keeper's P1 dispatch per `CC_REGULAR` plant (sum of tranches, pmax =
P1 fleet pmax); measured = CAMPD unit-level gross load summed per EIA plant (after
`CAMPD_UNIT_PLANT_REMAP`), 21 of 22–23 plants covered; Ravenswood 2500 excluded
from shape statistics (its CAMPD facility is the whole steam station, p99.5 =
6.8 × the CC pmax — a boundary misalignment, rule 14's named exception).

**Claim "running hot over 80 % CF" — CONFIRMED at plant-hour grain in 2024 and
2025, not 2023; and the excess sits in the 80–90 % bin, BELOW the duct wall:**

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| plant-hours > 80 % of pmax, model / measured | 43,903 / 44,558 | 58,298 / 49,047 | 59,807 / 46,306 |
| plant-hours > 90 %, model / measured | 20,677 / 30,068 | 29,532 / 33,972 | 31,276 / 30,226 |
| TWh delivered above 80 %, model / measured | 20.62 / 20.53 | 24.98 / 25.04 | 21.09 / 21.43 |
| TWh delivered above 90 %, model / measured | 9.57 / 14.71 | 10.81 / 18.00 | 9.40 / 15.17 |
| online plant-hours, model / measured | 92,435 / 89,679 | 111,107 / 91,003 | 121,036 / 96,546 |

MW-weighted share of online plant-hours by loading bin (model / measured):

| bin | 2023 | 2024 | 2025 |
|---|---|---|---|
| 80–90 % | **27.9 / 6.0** | **33.0 / 5.8** | **26.8 / 7.1** |
| 90–100 % | 18.6 / 27.6 | 19.7 / 33.9 | 16.6 / 27.1 |
| 20–50 % | 16.8 / 14.1 | 14.0 / 15.7 | 19.3 / 20.4 |

The model parks the class in the 80–90 % band 4–5× as often as the real fleet and
reaches 90–100 % too rarely — the `docs/cc-high-cf-investigation.md` "right
ceiling, wrong distribution" signature. The 80–90 % pile-up is at the plants whose
duct wall (the peak tranche's lower edge, `1 − pct_peak`) sits inside that band —
Astoria II 57664 (wall 83.1 %), CPV Valley 56940 (84.9 %), Saranac 54574 (83.3 %),
Bethpage 50292 (71.8 %) — plus Bethlehem 2539 (wall 91.0 %; model 6,060 h in
80–91 % vs measured 3,190 h above 90 %) and Zeltmann 56196 (no wall at all).

**Claim "runs more often at lower CF" — CONFIRMED as online hours (2024/2025: +20–25 k
plant-hours online in the model) and as the peak tranche being MARGINAL for
thousands of hours** (57664: 4,337 h at 92 of 110 MW; 55375: 4,734 h in 2024).

**The duct band's SIZE vs measured conduct.** `cc_duct_peaking` sizes each plant's
peak band from the EIA-860 nameplate-minus-net-summer gap: Cricket Valley 22.6 %,
Bethpage 28.2 %, Astoria II 16.9 %, Saranac 16.7 %, CPV 15.1 %. The same plants'
CAMPD reach — capacity used in fewer than 5 % of online hours, the
`derive_thermal_tranches.py` `peaking_pct` already in
`thermal_tranches-perunitmerit-NYISO.csv` — reads 5.7 / 5.8 / 0.6 / 25.0 / 2.1 %,
and the real plants exceed their 860-implied "unfired" capability for 2,000–6,400 h
a year (cap-weighted 2,835 / 2,387 / 2,009 h vs the model's peak-tranche 1,081 /
1,952 / 1,680 h). The 860 gap conflates the ambient summer derate with the duct
increment (the field's own docstring; miso-193 §1) — the wall is too LOW at these
plants.

**The duct band's PRICE vs measured conduct — no measured identification for an
upward move:** (a) CAMPD incremental heat rate in the top loading band relative to
the base band (OLS slope ratio, plant's own p99.5 basis) is 1.0–1.5×, not 2.25×
(55375 1.42 / 1.52; 57664 1.21 / 1.28; 56940 1.27 / 1.18; 2539 1.09 / 0.96 in
2024 / 2025); band-mean heat rates barely differ. (b) The RT LBMP at which real
duct firing appears equals the LMP at which the model's peak tranche clears:
cap-weighted median LBMP in measured duct hours 32.8 / 35.1 / 60.9 $/MWh vs model
peak-tranche hours 38.3 / 36.2 / 58.6. The measured PREMIUM over each plant's own
base-load hours is larger (1.18 / 1.18 / 1.40 vs 1.08 / 1.02 / 1.04) because the
real plants run base load in cheaper hours, not because the wall is priced lower.

**Consequence for the lane.** The owner's observed symptom is real and measured; the
top-band merit order IS wrong. But the measurement locates the error in the band's
SIZE (wall placement) and in the econ ramp's behaviour below it, not in the wall's
HEIGHT: raising the peak offer cannot move mass out of the 80–90 % bin — it can only
move mass INTO it from 90–100 % (the plant stops at the wall) — i.e. away from the
measured distribution, while lowering `CC_REGULAR` energy by at most the peak-band
energy (0.70 / 1.15 / 0.80 TWh non-duty). A lower C1-2024 residual reached that way
is exactly what rule 1 `[R-STRUCT]` forbids. No measured quantity identifies a peak
multiplier above the registered physical 2.25 (rules 13 / 21), so an upward level
would be a free parameter.

## 2. The two screens (rule 29: one year each, structural STOP gates only)

**Screen year = 2024** — the year of the mechanism's largest measured footprint:
non-duty peak-tranche energy 0.70 / **1.15** / 0.80 TWh and tranche-hours 10.8 k /
**18.3 k** / 17.7 k (2023 / 2024 / 2025). It is chosen on the footprint census
above, not on any residual; that 2024 is also the C1 fail year is noted and is not a
gate input.

**Control = the keeper's committed 2024 (form 4).** G-DRIFT `d5bba63b..HEAD` on the
solve path, every hunk classified INERT for a NYISO backcast: `offer_curves.py`
(`miso_intermediate_gas_offer_margin`, MISO-gated and default off);
`iso_configs.py` (PJM overrides; the two NYISO `default_scenario_overrides`
`nyiso_requirement_forecast_peak` / `nyiso_requirement_vintage_factors` are consumed
only in `capacity_evolution/retirements.py`, never entered in `mode="backcast"`, and
the replay runs the bundle's recorded config, which carries them `False`);
`scenarios.py` (`ccs_retrofit_capex_co2_scaling` default flip — `ccs.py` returns
before 2028; `miso_intermediate_gas_offer_margin`;
`capacity_market_supply_clearing_by_iso` — capacity market); `runner.py` /
`constants.py` / `capacity_market.py` / `adequacy.py` / `ccs.py` / `evolve.py` /
`retirements.py` (capacity evolution / clearing, forecast-only); `cache.py`
(cache-key epoch accounting); `run_calibration_full.py` (a `None`-default
override kwarg). No control solve is spent.

### Arm S — the measured form of the owner's object: `cc_duct_peaking_cap_pct = 8.0`
`scripts/replay_keeper.py results/calibration/nyiso192_astoria_panel --years 2024
--set cc_duct_peaking_cap_pct=8.0 --out-dir results/calibration/nyiso194_screen_cap8_2024`.
Single registered field, zero free parameters: 8.0 is the F-class supplementary-firing
engineering maximum already carried as PJM's default (`pipeline/backcast_config.py`),
identified from engineering practice, never from a residual. Rule 25: MISO tested the
same field in its own lane (miso-193, rejected on MISO's K-1) — no verdict transfers;
this is NYISO's own test. Static reach on the 2024 fleet (duty-split cohort excluded —
`cc_reserve_duty_split` / `chp_layup_*` re-band LAST and are untouched): `CC_REGULAR`
57185 245.6 → 87.0 MW, 57664 109.8 → 52.0, 56940 105.1 → 55.7, 50292 50.6 → 14.4,
54574 42.0 → 20.1, 2539 80.4 → 71.4, 56234 32.9 → 28.9, 56188 7.5 → 6.6 (≈ 338 MW
moves from the peak band to the econ ramp); `CC_CHP` duct-flagged plants with gap > 8
(54547 160.9 MW, 56259 73.9, 10725 50.6, 50458 21.5, 10617, 50450, 50451, 54076,
54131) are in reach too unless a lay-up/duty cohort re-band supersedes — the arm's
fleet parquet is the census of record.

Gates (STOP only; the screen never promotes):
- **S-1 footprint.** Only `_peak` / econ tranche pmax at plants with an EIA-860 gap
  > 8 change; every other unit's tranche pmax is byte-identical to the keeper's 2024
  fleet parquet.
- **S-2 identity.** At each capped `CC_REGULAR` plant, peak-band pmax = 8 % of grid
  capacity within rounding (the field's own arithmetic).
- **S-3 direction (the mechanism does what its arithmetic says).** At the capped
  wall-in-80–90 % plants (57664, 56940, 54574, 50292) plant-hours above the OLD wall
  rise and the MW-weighted 80–90 % share falls / 90–100 % rises — toward the CAMPD
  distribution. STOP if the class 80–90 % share does not fall.
- **S-4 no non-target load-bearing flip on 2024.** C2, C3a, C3b hold PASS on the
  screen year (computed from the screen's system parquet against the same actuals;
  the full-span registration is the scored record). C1-2024 is the target-adjacent
  cell and already FAIL on the keeper — reported, never gated; C8 reported.

### Arm D — the owner's literal direction as an explicitly-labelled DIAGNOSTIC: `CC_REGULAR.peak` 2.25 → 2.50
`scripts/replay_keeper.py results/calibration/nyiso192_astoria_panel --years 2024
--offer-curve-json '{"CC_REGULAR": {"peak": 2.5}}' --out-dir
results/calibration/nyiso194_screen_peak250_2024`. 2.50 is the registry's own next
physical bucket (`CC_DUCT_BURNER_PEAK_MULT["advanced"]`, G/H-class), the only
upward value in the registry not typed for this test; it is NOT a NYISO-measured
value, so this arm is a diagnostic of the DIRECTION and can never be a keeper
candidate without an owner-ruled DOF entry (rule 21). Arithmetic under the armed
`gas_offer_net_revenue_margin`: `phys_peak` stays 2.25, so the +0.25 enters every
`CC_REGULAR` `_peak` tranche (duty-cohort peak bands included) as a fuel-invariant
margin `0.25 × base HR × 3.9046` ≈ +$6–7/MWh; no other band moves.

Gates:
- **D-1 footprint.** Only `CC_REGULAR` `_peak` tranche offers change (fleet parquet
  byte-identical; the dispatch delta concentrates in those tranches).
- **D-2 direction (phase-0 prediction, pre-registered).** Peak-tranche energy and
  tranche-hours FALL; at the wall-in-80–90 % plants the 80–90 % share RISES and the
  90–100 % share falls — AWAY from CAMPD; `CC_REGULAR` energy falls by ≤ the
  peak-band energy. If the shape moves away from measured as predicted, the
  direction is KILLED as a candidate on the structural gate (a mechanism whose
  effect is a shape the measurement contradicts), and the result is reported to
  the owner as the evidence behind §1's conclusion. If the shape moves TOWARD
  CAMPD, phase 0's reading is wrong and the finding says so.

### Disposition rule (frozen)
- Arm S clears S-1..S-4 → the full 2023–2025 span is solved as ONE bundle,
  registered, attested (G-CTRL form 4 against the keeper), scored; promotion is the
  owner's call under the standing formula with the determination stated.
- Arm S fails any gate → no full span; finding + matrix cell + log.
- Arm D is never promoted from this PREREG whatever it shows; its screen bundle is a
  throwaway probe (rule 29 / rule 16), never registered.
- Nothing here is gated on C1-2024 or on any residual.

*(nyiso-194, 2026-09-05. Pushed before either screen was launched.)*
