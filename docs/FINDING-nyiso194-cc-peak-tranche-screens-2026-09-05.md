# FINDING nyiso-194 — the `CC_REGULAR` duct-burner peaking tranche: phase 0 and two one-year screens, BOTH KILLED on their pre-registered structural gates (2026-09-05)

**Owner ruling under test** (in session, 2026-09-05): *"tune the cc regular offer curve
up for the duct burner peaking tranche because it's merit order is wrong it runs more
often at lower CF and is running hot over 80% CF in all years."*
**Keeper / control:** `2026-09-05-nyiso-192-astoria-panel` (rule 29(b) form 4; G-DRIFT
all INERT, PREREG §2). **Pre-registration:**
`results/calibration/PREREG-nyiso194-cc-peak-tranche-screen.md`, pushed at `aa3038d1`
before either screen was launched. **Keeper unchanged. No full span solved. Nothing
registered** (rule 29: a screen bundle is a throwaway probe; both stay local).

## 1. The symptom is real and measured (phase 0, zero LP)

`scripts/probes/nyiso194_cc_peak_phase0.py` → `_nyiso194_cc_peak_phase0.json`. The
class's MW-weighted loading distribution (share of online plant-hours by 10 % bin of
pmax, Ravenswood 2500 excluded as a CAMPD boundary misalignment):

| | 80–90 % model / CAMPD | 90–100 % model / CAMPD | online plant-h model / CAMPD |
|---|---|---|---|
| 2023 | **27.9 / 6.0** | 18.6 / 27.6 | 92,435 / 89,679 |
| 2024 | **33.0 / 5.8** | 19.7 / 33.9 | 111,107 / 91,003 |
| 2025 | **26.8 / 7.1** | 16.6 / 27.1 | 121,036 / 96,546 |

The model parks combined cycles in the 80–90 % band 4–5× as often as the real fleet and
reaches 90–100 % too rarely; in 2024/2025 it also keeps them online 20–25 k more
plant-hours. Both halves of the owner's observation hold. The pile-up sits **below** the
duct wall (`1 − pct_peak`): Astoria II 57664 (wall 83 %), CPV 56940 (85 %), Bethlehem
2539 (91 %: 6,060 h in 80–91 % vs CAMPD 3,190 h above 90 %), and Zeltmann 56196 with
no wall at all (37 % of hours in 80–90 % vs 10 % measured).

**No measured quantity identifies a HIGHER peak offer** (PREREG §1): the CAMPD
incremental heat rate of the top loading band is 1.0–1.5× the base band (not 2.25×), and
the RT LBMP at which real duct firing appears (cap-weighted median 32.8 / 35.1 / 60.9
$/MWh) equals the LMP at which the model's peak tranche already clears (38.3 / 36.2 /
58.6). The measured premium over each plant's own base-load hours is larger (1.18 / 1.18
/ 1.40 vs the model's 1.08 / 1.02 / 1.04) because real plants run base load in cheaper
hours, not because the wall is priced low. The band's SIZE, by contrast, is measurably
wrong: the EIA-860 nameplate-minus-net-summer gap (Cricket Valley 22.6 %, Bethpage 28.2 %,
Astoria II 16.9 %) vs the plants' own CAMPD reach (5.7 / 5.8 / 0.6 %), and real plants
exceed their 860-implied unfired capability 2,000–6,400 h/yr (cap-weighted 2,835 / 2,387 /
2,009 h vs the model's peak tranche 1,081 / 1,952 / 1,680 h).

## 2. Screen year 2024 (largest measured footprint: non-duty peak-band energy 0.70 / 1.15 / 0.80 TWh)

Gate evaluator: `scripts/probes/nyiso194_screen_gates.py` (self-checked zero-delta on
the keeper) → `_nyiso194_screen_gates_S.json`, `_nyiso194_screen_gates_D.json`.

### Arm S — `cc_duct_peaking_cap_pct = 8.0` (the measured form; physical F-class bound) — KILLED on S-3

- **S-1 footprint PASS:** 77 tranche-pmax changes, all at the 11 plants with an 860 gap
  > 8 (`CC_REGULAR` 57185, 57664, 56940, 50292, 54574, 2539, 56234, 56188; `CC_CHP`
  54547 Sithe, 56259, 50458); every other unit byte-identical.
- **S-2 identity PASS:** peak band = 8.00 % of plant capacity at every capped
  `CC_REGULAR` plant.
- **S-3 direction FAIL (the frozen STOP):** at the four wall-in-80–90 % plants, hours
  above the OLD wall rose 2,199 → 9,643 (CAMPD 12,935) — the cap does what its
  arithmetic says — **but the class 80–90 % share ROSE 33.0 → 36.3 % (CAMPD 16.5) and
  90–100 % fell 19.8 → 18.9 % (CAMPD 33.9).** The plants moved up to the new 92 % wall
  and parked just below it (56940: >old-wall 189 → 4,283 h, >90 % 189 → 138 h; 2539
  80–90 % share 74.9 → 87.2 %). Peak-band energy 1,253 → 721 GWh; `CC_REGULAR` +0.86 TWh,
  `ST_GAS` −0.41, `CC_CHP` −0.14, `CT_CHP` −0.14 (the fill runs the other way).
- **S-4 companions (approximate, same-weights construction):** load-weighted mean price
  −0.72 % → −3.05 % vs actual; monthly NRMSE 0.183 → 0.188; gas family 68.22 → 68.26 TWh.
  Not gated (S-3 already killed the arm).

### Arm D — `CC_REGULAR.peak` 2.25 → 2.50 (the owner's literal direction, diagnostic) — KILLED on D-2

- **D-1 footprint PASS:** fleet parquet byte-identical (0 pmax changes); the dispatch
  delta sits in the `_peak` tranches (+$6–7/MWh fixed margin under
  `gas_offer_net_revenue_margin`, `phys_peak` 2.25 unchanged).
- **D-2 direction — the phase-0 prediction HELD:** peak-tranche energy 1,253 → 680 GWh,
  tranche-hours 20,745 → 11,746; at the wall plants hours above the wall fell 2,199 → 989
  (CAMPD 12,935); **class 90–100 % share fell 19.8 → 17.2 % (CAMPD 33.9) — AWAY from
  the measured distribution**; 80–90 % 33.0 → 32.0 % (CAMPD 16.5; a one-point move, the
  mass leaving the top lands at the wall: 57664 80–90 % 61.5 → 71.6 %). `CC_REGULAR`
  −0.45 TWh (≈ −0.37 pp — it would bring C1-2024 inside the 3.0 pp band), `ST_GAS` +0.18,
  `CC_CHP` +0.15. **That residual gain is reached by moving the class's loading shape
  further from CAMPD with a level no measurement identifies — the rule 1 `[R-STRUCT]`
  case exactly, and the reason this arm was pre-registered as a diagnostic that can
  never be a candidate.**
- Companions: load-weighted mean price −0.72 % → +0.20 %; NRMSE 0.183 → 0.186.

Both screens carry the keeper's own D-4 rider rows (`reliability_floor` /
`nyiso_gas_commitment_bridge` × `ST_GAS` at 2480 / 2500 / 8906) — unchanged, not new.

## 3. What the two screens together locate

Neither the wall's price (Arm D) nor the wall's placement (Arm S) moves the class out of
the 80–90 % band: the LP parks each plant where its **econ ramp's marginal slice** meets
the LMP (`offer_curve_smoothing_n = 6` slices from `econ_low 0.95` to `econ_high 1.0` ×
base HR), and the real fleet has no such operating point — it runs at full load or at
part load (CAMPD 20–50 % + 90–100 % = 48 % of hours; 80–90 % = 6 %). The measured
physical basis NYISO already registers says the top of the ramp is CHEAPER at the
margin than the middle, not dearer: `phys_econ_low 0.784 → phys_econ_high 0.925`
(`nyiso_campd_marginal_hr_summary.csv` p50s), while the registered offer ramp rises
0.95 → 1.0 and the net-revenue margin converts the difference into a falling fixed
markup. The next measured object is therefore the **econ ramp's shape**, not the peak
band: offer the econ block at its own measured marginal heat-rate basis (a measured,
already-registered, zero-DOF construction — rules 13 / 14 / 21), and test whether the
80–90 % mass moves to 90–100 %. Handed forward as the top of the §5.5 queue; NOT run
here (this session's two screens are spent, and the object needs its own PREREG).

## 4. Disposition

- **No keeper candidate from nyiso-194.** Keeper `2026-09-05-nyiso-192-astoria-panel`
  unchanged (NOT-YET; `complete` / `frontier` withdrawn by the promotion, same day).
- **Owner's directed lever (peak offer UP): tested in its own lane on one year as a
  diagnostic and REJECTED on shape** — it lowers the C1-2024 residual only by moving
  the class's loading distribution further from CAMPD, with no measured identification
  for the level. Matrix `offer_curve_by_group` NYISO cell annotated (K unchanged for the
  registered curve; the upward-peak direction R with this citation);
  `cc_duct_peaking` NYISO cell: the 8 % cap R in NYISO's own lane (S-3), the field
  itself stays K as armed on the keeper.
- **Cost:** two one-year screens (~25 min each, concurrent); zero full-span solves.

*(nyiso-194, 2026-09-05. Screen bundles `results/calibration/nyiso194_screen_cap8_2024`,
`nyiso194_screen_peak250_2024` are local throwaway probes — never registered.)*
