# NYISO CT_PEAKER: the measured heat rate lands — and it is 2.5x smaller than nyiso-88 measured

**Session:** nyiso-89 (CT heat-rate input) · **Date:** 2026-07-27
**Premise:** `docs/FINDING-nyiso88-peaker-heat-rate-2026-07-27.md` §4 / §7 step 1
**Mode:** input build + one registered arm against a same-HEAD zero-delta control

---

## 0. Summary

nyiso-88 identified a real measured-input defect: the non-ERCOT fleet prices
every combustion turbine on an **eGRID plant-average annual** heat rate, which
is neither a loaded rate nor — at a mixed facility — the right technology's
rate. This session built the measured replacement
(`scripts/data/derive_campd_ct_heat_rates.py`), wired it in ahead of the eGRID
value under `ScenarioConfig.measured_ct_heat_rates`, and solved one arm against
a same-HEAD zero-delta control.

Two results, and the second is a correction to the premise this session was
given.

1. **The input defect is real and the fix is structurally right.** The eGRID
   value is wrong per-plant by −$42 to +$82 per MWh at 2025 gas, in **both**
   directions. It is source noise, not a bias, so the fix is a **merit-order
   reordering inside the class** — the modern in-city turbines get cheaper, the
   1970s FT4 barges get dearer — not a discount (§2).

2. **The bias is 2.5x smaller than nyiso-88 reported, because §4 mixed bases.**
   CAMPD meters **gross** load; eGRID's heat rate, the LP's dispatched MW and
   the benchmark's own actual are all **net**. Corrected onto a common net
   basis, the generation-weighted SRMC bias is **+$1.37 / +$1.49 / +$2.50 per
   MWh**, not the **+$6.48 / +$6.70 / +$7.34** §4 published (§1). The premise's
   headline — "the cost error exceeds the margin the fleet actually earns, in
   every year" — **does not survive the correction**: against the measured
   fleet margin of −$1.39 / +$5.82 / +$3.49, the bias is comparable in 2023 and
   clearly smaller in 2024 and 2025.

The input stays regardless (rule 14 [R-ACCURATE], rule 1 [R-STRUCT]): it is the
accurate input and the eGRID value it replaces is a known-defective estimate.
But it was never going to close the CT_PEAKER volume gap on its own, and after
the correction in §1 it is no longer even the leading candidate to.

---

## 1. The basis correction — recorded up front, as nyiso-88 recorded its own

nyiso-88 §1 opens with a correction to its own first pass (pricing the fleet on
the superseded firm city-gate gas stand-in). This section is the same kind of
disclosure about §4 of that same document.

`nyiso88_peaker_economics.measured_loaded_heat_rate` returns
`heatInput / grossLoad`. CAMPD's `grossLoad` is generator-terminal **gross**
output. Everything it was compared against is **net**:

* eGRID's plant heat rate — the model's `heat_rate` — is per net MWh;
* the LP dispatches net MW;
* the benchmark's per-plant actual is built as `gross × parasitic_factor` by
  `run_calibration_full._campd_hourly_frame`.

Dropping the station-service fraction is worth 1 % on a bare CT — and **10.2 %
at Bayonne Energy Center**, the largest plant in the class and 41 % of its
energy, whose committed parasitic factor is 0.898 (measured, `ok`-flagged,
consistent at 0.88–0.92 across 2022–2025 against a matching EIA-923 / CAMPD unit
set — audited this session, not a coverage artifact).

Restated on the common net basis
(`scripts/probes/nyiso89_ct_heat_rate_basis.py`):

| weighting | model | measured (gross, §4's basis) | measured (net) | model/net |
|---|--:|--:|--:|--:|
| capacity | 11.856 | 11.720 | 12.077 | **0.982** |
| generation | 11.014 | 10.247 | 10.682 | **1.031** |

and in $/MWh at the keeper's own delivered downstate-CT gas:

| year | gas $/MMBtu | bias, gen-wtd **net** | bias, gen-wtd gross (§4) | measured fleet margin (nyiso-88 §3) |
|---|--:|--:|--:|--:|
| 2023 | 4.12 | **+1.37** | +3.16 | −1.39 |
| 2024 | 4.50 | **+1.49** | +3.45 | +5.82 |
| 2025 | 7.54 | **+2.50** | +5.77 | +3.49 |

(§4's published +$6.48/+$6.70/+$7.34 are larger still than the gross-basis
column here because §4 also restricted to *pure*-CT plants and weighted by each
year's bench series; the direction and the cause of the gap are the same.)

**Capacity-weighted, the model does not overcharge the class at all — it
undercharges it by $0.91–$1.66/MWh.** The generation- and capacity-weighted
numbers move in opposite directions, and only the pair states the effect
honestly: the model overcharges the plants that actually run and undercharges
the ones that barely do.

---

## 2. What the input actually changes: reordering, not discounting

Nineteen plants (2,395 MW, 91.6 % of class capacity) carry a measured rate.
Fourteen get **cheaper** (921 MW), five get **dearer** (1,475 MW).

| plant | MW | model | measured (net) | Δ HR | Δ $/MWh @2025 gas |
|---|--:|--:|--:|--:|--:|
| Bayswater Peaking Facility | 55.8 | 21.68 | 10.74 | −10.94 | **+82.45** |
| Port Jefferson | 82.7 | 12.01 | 9.33 | −2.69 | +20.23 |
| Hell Gate | 79.5 | 11.25 | 9.77 | −1.48 | +11.15 |
| 23rd and 3rd | 79.9 | 11.23 | 9.90 | −1.33 | +10.01 |
| Pouch Terminal | 44.7 | 10.87 | 9.64 | −1.24 | +9.33 |
| North 1st | 46.0 | 11.00 | 9.77 | −1.22 | +9.23 |
| Brentwood | 45.0 | 10.85 | 9.65 | −1.20 | +9.05 |
| Vernon Boulevard | 79.9 | 10.92 | 9.74 | −1.17 | +8.85 |
| Harlem River Yard | 79.5 | 10.75 | 9.64 | −1.12 | +8.41 |
| Bethpage Energy Center | 44.1 | 9.82 | 10.28 | +0.47 | −3.51 |
| Bayonne Energy Center | 598.1 | 9.77 | 10.28 | +0.51 | −3.82 |
| Gowanus | 282.0 | 15.04 | 15.28 | +0.24 | −1.83 |
| Narrows | 269.0 | 15.16 | 15.75 | +0.60 | −4.51 |
| **E F Barrett** | 281.4 | 11.08 | **16.69** | +5.62 | **−42.32** |

(Full table: `data/raw/_processed-legacy/campd_ct_heat_rates_NYISO.csv`.)

Two structural corrections dominate, and they pull opposite ways:

* **Bayswater at 21.68 MMBtu/MWh is not a physical simple-cycle heat rate.**
  Measured, it is 10.74. The model was charging that plant roughly double its
  true fuel cost.
* **E F Barrett's turbines were being priced as its steam boilers.** eGRID's
  single 11.076 for plant 2511 blends 1971 FT4 twin-pacs with 188 MW of gas
  steam. Measured separately the turbines run **16.69** — the model was
  *undercharging* 281 MW of genuinely inefficient peaking iron by 34 %.

The whole in-city modern CT fleet (Vernon, Hell Gate, Harlem River Yard, 23rd
and 3rd, North 1st, Brentwood, Pouch Terminal, Port Jefferson) moves **down**
the merit order by $8–20/MWh at 2025 gas, while the 1970s barge fleet (Barrett,
Gowanus, Narrows) moves **up**. That is the mechanism to judge this input on —
the class total is a poor summary of it.

---

## 3. The input

`scripts/data/derive_campd_ct_heat_rates.py --iso NYISO`, per CAMPD unit over
the pooled 2023–2025 window:

```
cap      = p95 of the unit's own gross load
loaded   = hours with grossLoad >= 0.80 x cap        (>= 50 qualifying hours)
hr_gross = sum(heatInput) / sum(grossLoad) over `loaded`
hr_net   = hr_gross / parasitic_factor(plant)
```

plant value = generation-weighted mean of its turbines' `hr_net`.

Restricted to CAMPD `unitType == "Combustion turbine"`, which is what lets a
mixed steam/CT facility contribute **only its turbines** instead of being
dropped as unattributable — the choice `derive_campd_gas_commitment_params.py`
is forced into, because its statistic has no equivalent technology tag. Barrett
is exactly the case that needs this.

The parasitic factor is the **same committed artifact the benchmark uses**
(`parasitic_load_factors.parquet`), so the derived rate and the generation it
will be scored against share one gross-to-net convention.

Rates outside the physical simple-cycle band [6.0, 25.0] MMBtu/MWh are written
with a `flag` and **excluded from the applied map** — a data-integrity guard on
the meter, not a tuning knob. No NYISO plant is currently flagged. The 23
uncovered plants (219 MW: the tail below ~45 MW plus fuel cells and small
municipal turbines with no qualifying CEMS-loaded hours) keep their eGRID rate.

**Wiring.** `ScenarioConfig.measured_ct_heat_rates` (default **off**), applied
in `fleet/eia860.py::_rows_to_generators` **after** the row's `plant_group` is
resolved and ahead of the eGRID value — so only `CT_PEAKER` rows are repriced
and a mixed plant's steam and CC rows are untouched. Verified in
`tests/unit/data/test_measured_ct_heat_rates.py`, which also asserts all three
`fleet.assembly` call sites forward the flag (a call site that forgets it would
silently solve on eGRID rates while `run_config.json` claimed otherwise — a
failure invisible in the LP output).

**Admissibility.** Rule 13 [R-MEASURED]: a machine's loaded heat rate is a
physical characteristic that regenerates for a forward year from the same
pipeline and responds to changed conditions (a retrofit moves it; a new unit
carries its design rate). It is not a measured *outcome* fed back to close a
residual, and no parameter of the construction was chosen by looking at one.
Rule 24 [R-FROZEN-DERIVE]: re-derives only on a CAMPD vintage change.

---

## 4. Arm vs control

Two registered runs, same HEAD, same keeper recipe, differing in exactly one
`ScenarioConfig` field:

* `2026-07-27-nyiso-89-control-zerodelta` (`results/calibration/nyiso89_ctrl_zerodelta`)
* `2026-07-27-nyiso-89-ctmeas-hrloaded` (`results/calibration/nyiso89_hrmeas_ctloaded`)

The control reproduces the keeper exactly (CT_PEAKER 0.459 / 0.314 / 1.282 TWh
against the keeper's published 0.46 / 0.31 / 1.28; D-1 `profile_r`
0.876 / 0.928 / 0.949), so the deltas below are attributable to the input swap
alone.

### 4a. A wiring defect that had to be caught first

**The first arm came back byte-identical to its control** — every class, every
hour of 2023, max absolute difference exactly `0.0` — for a change that moves
individual plant heat rates by up to 10.9 MMBtu/MWh.

`scripts/run_calibration.py::run_year` does **not** call
`fleet.assembly.load_or_synthesize_bins`. For the non-ERCOT per-plant ISOs it
inlines its own `fleet_to_bins(load_fleet_from_csv(...))`, and that call did not
forward the new flag. Since CT_PEAKER plants are binned, the bins are the *only*
path their cost reaches the LP by — so the solve ran on eGRID rates while
`run_config.json` recorded the measured input as on.

This is worth recording because of how it fails: it does not look broken, it
looks like **"the mechanism is inert."** Reported without an exact-equality
check it would have become a confident and completely wrong structural finding.
The fix forwards the flag, and the regression test parses
`run_calibration.py` and asserts **every** `load_fleet_from_csv` call in it
forwards it, so the next fleet-sourcing flag cannot repeat this silently.

All numbers below are from the re-solved arm, whose P0 commitment pattern
differs from the control's (2023: 20,077 → 19,940 unit-hours floored) — the
mechanism is demonstrably live.

### 4b. Result: the input is nearly inert, and inconsistent in sign

| year | CT_PEAKER control | arm | delta | actual | gap closed |
|---|--:|--:|--:|--:|--:|
| 2023 | 0.459 | 0.443 | **−0.016** | 2.260 | **−0.9 %** (worse) |
| 2024 | 0.314 | 0.394 | **+0.080** | 2.134 | +4.4 % |
| 2025 | 1.282 | 1.407 | **+0.125** | 3.011 | +7.2 % |

The energy is a near-pure swap with **ST_GAS** (+0.025 / −0.078 / −0.087),
with CC_REGULAR and oil making up the remainder; system totals are unchanged to
three decimals in all three years.

**2023 moves the wrong way.** That is the capacity-weighted arithmetic of §1
showing up in dispatch: correcting E F Barrett *upward* (11.08 → 16.69 on
281 MW) removes more capacity from merit than Bayswater (21.68 → 10.74 on
56 MW) and the in-city fleet add back. Which effect wins depends on where the
year's prices sit relative to each plant's new SRMC, so the sign is not stable
across years — exactly what "source noise in both directions" implies.

### 4c. Gate re-score — C1 and C5a as instructed

Every criterion verdict is **identical** between arm and control. Determination
**NOT-YET** for both (governance UNATTESTED — these are probes, not keeper
candidates).

| criterion | control | arm |
|---|---|---|
| C1 fuel-mix | PASS (14/14, free 10/10) | PASS (14/14, free 10/10) |
| C2 / C3a / C3b / C4 / C7 / C8 | PASS | PASS |
| C3c price tail | FAIL 3 / 0 / 6 h vs 10 / 12 / 42 | FAIL 3 / 0 / **7** h vs 10 / 12 / 42 |
| C5a CO2 | CAVEAT 2025 +7.6 % | CAVEAT 2025 +7.6 % |

**C1's thin margin (the flagged risk).** 2023 CC_REGULAR — the keeper's binding
cell — goes **−2.775 → −2.784 TWh** against a ±2.94 band. The margin thins from
0.165 to 0.156 TWh, about 5 % of the remaining headroom. It still PASSES, but
the cell is marginally *worse*, and it is worth stating plainly that this
criterion is one small adverse change away from flipping.

**C5a moves UP, and it was measured rather than assumed.** The brief noted CO2
moves twice here — more gas volume, but a lower heat rate on the CT fleet — and
warned not to assume the sign. Measured, the two do not cancel and the net is
slightly **positive**: 2025 system CO2 **31.376 → 31.390 Mt** against a 29.167
actual, i.e. **+7.57 % → +7.62 %**, still inside the ±10 % commercial band.
2023 (+0.50 → +0.50 %) and 2024 (+1.14 → +1.14 %) are nil. The mechanism is
that the energy CT_PEAKER gains comes from **ST_GAS and CC_REGULAR**, which
burn at lower heat rates than a peaker — so the volume effect dominates the
rate effect. The margin against the band is unchanged for practical purposes.

**Shape is neutral.** CT_PEAKER D-1 `profile_r` 0.876 / 0.928 / 0.949 →
0.878 / 0.914 / 0.947; `cv_ratio` 1.38 / 1.07 / 1.15 → 1.40 / 1.18 / 1.15. D-2
forced share stays 0.0 % in every year (no mechanism floors this class). C8's
2024 ST_GAS grounded-above-budget note is unchanged (31.9 % → 32.0 %).

### 4d. Verdict on the arm — PROMOTED TO KEEPER 2026-07-27

**Owner decision:** promoted to the NYISO keeper on the standing instruction
that improved structural integrity can carry a keeper even where gates regress.
`2026-07-27-nyiso-89-ctmeas-hrloaded` replaces `2026-07-27-nyiso-87-cmeas-measured`.

Determination **NOT-YET** — the same determination class and the same sole
blocking criterion (C3c) as the keeper it replaces. C6 governance PASSES on a
UNION'd DOF ledger (19 entries, `n_residual` **unchanged** at 6: the entry adds
zero fitted scalars and *replaces* a defective estimate rather than adding a
degree of freedom). Audited clean by `calibration-keeper-auditor` (0 failures,
0 repairs).

**LOYO (rule 22).** The input carries no parameter fitted to any year — it is a
pooled 2023–2025 measured statistic, and all three years are scored in this one
bundle. Re-deriving the artifact leaving each year out is stable for **16 of 19
plants** (< 5 % spread) and never reverses the correction's sign on any plant
that carries its weight: Bayonne 0.5 %, Bayswater 1.0 %, Port Jefferson 2.8 %,
Barrett 6.1 % (16.07–17.09, never approaching the eGRID 11.08). It is **not**
stable on the two thin-sampled 1970s barge plants — Gowanus (16.5 % spread) and
Narrows (12.8 %) — where dropping 2025 reverses the sign versus eGRID. Both
carry only 0.09 and 0.22 TWh of measured energy across three years and sit far
out of merit at *every* fold value (13.2–16.2 MMBtu/MWh against a class base
near 10), so no gate moves. A minimum-energy screen for thin-sampled plants is
the named follow-up and is deliberately **not** added here: choosing a screen
after seeing the LOYO result would be a post-hoc parameter (rule 24).

**The input stays, and it is not promoted as a fix.**

It stays because rule 14 [R-ACCURATE] and rule 1 [R-STRUCT] require it: the
eGRID plant-average annual rate is a known-defective estimate — non-physical at
Bayswater, wrong-technology at Barrett — and the measured loaded rate is the
accurate replacement. A 0.156 TWh C1 margin instead of 0.165 is not a reason to
put a defective input back; it is a discovered root cause elsewhere.

It is not promoted as a fix because it does not act like one: −0.9 / +4.4 /
+7.2 % of the gap, with the sign reversing in 2023. That is consistent with §1
(the true bias is +$1.37 / +$1.49 / +$2.50 per MWh, not +$6.48 / +$6.70 /
+$7.34) and with nyiso-88's own honest bound (in-merit hour-share 5.1 → 6.8 /
8.1 → 11.2 / 12.6 → 15.4 % against the *actual* price). **Neither this session
nor nyiso-88 has produced a mechanism that closes CT_PEAKER's level**, and the
heat rate is now eliminated as the candidate rather than confirmed as one.

---

## 5. What this does not do, and what is next

* **It does not re-arm any floor.** The charter's hard constraint is honoured:
  nothing here proposes a windowed floor, a temperature boxcar, or a CT-scoped
  `reliability_floor` row.
* **It does not re-open a closed route.** The NYCA/East spin gate and the J/K
  ladders stay closed and default-off.
* **The §1 correction reopens the question nyiso-88 thought it had answered.**
  With the bias at +$1.37/+$1.49/+$2.50 rather than +$6.48/+$6.70/+$7.34, the
  heat rate is no longer large enough to explain a 1.8–2.1 TWh volume gap on its
  own. nyiso-88's own honest bound already said as much — correcting the heat
  rate lifts in-merit hour-share only 5.1→6.8 / 8.1→11.2 / 12.6→15.4 % against
  the *actual* price — and this session's arm is the direct measurement of it.
* **Day-ahead block commitment remains the standing candidate**, to be judged
  against the measured CT run-length distribution (median 4 h, mean 6.5–7.6 h,
  p90 14 h — `campd_ct_run_lengths_NYISO.csv`) rather than against the volume
  gap. That is the next session's question, now that the input underneath it is
  correct.
* **The nyiso-88 §5 bench multi-class collapse is untouched** and still needs
  its own cross-ISO lane with owner scoping.
